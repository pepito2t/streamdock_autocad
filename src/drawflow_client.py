import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import websocket

PROTOCOL_VERSION = 1
CONFIG_PARTS = ("ch.drawflow.desktop", "integrations.json")
CONNECT_TIMEOUT_S = 3
COMMAND_TIMEOUT_S = 20
OFFLINE = "Drawflow n'est pas joignable (application fermée ou API locale désactivée)."
LOCKED = "Drawflow est verrouillée : saisissez le code d'accès dans l'application."
NOT_CONFIGURED = "API locale de Drawflow désactivée : activez-la dans Paramètres → API locale."


class DrawflowError(Exception):
    pass


@dataclass(frozen=True)
class DrawflowConnection:
    port: int
    token: str

    @property
    def url(self) -> str:
        return f"ws://127.0.0.1:{self.port}"


@dataclass(frozen=True)
class DrawflowModule:
    id: str
    name: str


def config_path(environ: dict[str, str] = os.environ) -> Path | None:
    override = environ.get("STREAMDOCK_DRAWFLOW_CONFIG")
    if override:
        return Path(override)
    appdata = environ.get("APPDATA")
    return Path(appdata, *CONFIG_PARTS) if appdata else None


def parse_config(text: str) -> DrawflowConnection | None:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict) or not raw.get("enabled") or not raw.get("token"):
        return None
    port = raw.get("port")
    if not isinstance(port, int) or port <= 0:
        return None
    return DrawflowConnection(port=port, token=str(raw["token"]))


def load_connection(path: Path | None = None) -> DrawflowConnection | None:
    path = path or config_path()
    if path is None or not path.is_file():
        return None
    return parse_config(path.read_text(encoding="utf-8"))


class DrawflowClient:
    def __init__(self, connection: DrawflowConnection | None = None) -> None:
        self._connection = connection

    def run_feature(self, module_id: str, inputs: dict[str, Any]) -> Any:
        return self.command("feature.run", {"moduleId": module_id, "inputs": inputs})

    def list_modules(self) -> list[DrawflowModule]:
        state = self.command("app.state", {})
        modules = state.get("modules", []) if isinstance(state, dict) else []
        return [DrawflowModule(id=str(module["id"]), name=str(module["name"])) for module in modules]

    def command(self, name: str, args: dict[str, Any]) -> Any:
        connection = self._connection or load_connection()
        if connection is None:
            raise DrawflowError(NOT_CONFIGURED)
        socket = self._open(connection)
        try:
            self._handshake(socket, connection)
            return self._send_command(socket, name, args)
        finally:
            socket.close()

    def _open(self, connection: DrawflowConnection) -> websocket.WebSocket:
        try:
            return websocket.create_connection(connection.url, timeout=CONNECT_TIMEOUT_S)
        except (OSError, websocket.WebSocketException) as error:
            raise DrawflowError(OFFLINE) from error

    def _handshake(self, socket: websocket.WebSocket, connection: DrawflowConnection) -> None:
        reply = self._exchange(socket, {"type": "hello", "token": connection.token, "version": PROTOCOL_VERSION})
        if reply.get("type") != "welcome":
            raise DrawflowError(str(reply.get("message") or OFFLINE))
        if reply.get("locked"):
            raise DrawflowError(LOCKED)

    def _send_command(self, socket: websocket.WebSocket, name: str, args: dict[str, Any]) -> Any:
        command_id = uuid.uuid4().hex
        socket.settimeout(COMMAND_TIMEOUT_S)
        socket.send(json.dumps({"type": "command", "id": command_id, "command": name, "args": args}))
        while True:
            reply = self._receive(socket)
            if reply.get("type") == "result" and reply.get("id") == command_id:
                break
        if not reply.get("ok"):
            raise DrawflowError(str(reply.get("error") or "Drawflow a refusé la commande."))
        return reply.get("data")

    def _exchange(self, socket: websocket.WebSocket, message: dict[str, Any]) -> dict[str, Any]:
        socket.send(json.dumps(message))
        return self._receive(socket)

    def _receive(self, socket: websocket.WebSocket) -> dict[str, Any]:
        try:
            raw = socket.recv()
        except (OSError, websocket.WebSocketException) as error:
            raise DrawflowError(OFFLINE) from error
        try:
            reply = json.loads(raw)
        except json.JSONDecodeError as error:
            raise DrawflowError("Réponse illisible de Drawflow.") from error
        return reply if isinstance(reply, dict) else {}
