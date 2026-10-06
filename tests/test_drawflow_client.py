import json

import pytest

from src.drawflow_client import DrawflowClient, DrawflowConnection, DrawflowError, parse_config


class FakeSocket:
    def __init__(self, replies: list[dict]) -> None:
        self.replies = list(replies)
        self.sent: list[dict] = []
        self.closed = False

    def settimeout(self, value: float) -> None:
        pass

    def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))

    def recv(self) -> str:
        return json.dumps(self.replies.pop(0))

    def close(self) -> None:
        self.closed = True


def make_client(monkeypatch, replies: list[dict]) -> tuple[DrawflowClient, FakeSocket]:
    socket = FakeSocket(replies)
    client = DrawflowClient(DrawflowConnection(port=51717, token="t" * 48))
    monkeypatch.setattr(client, "_open", lambda connection: socket)
    return client, socket


def test_parse_config_requires_enabled_and_token():
    assert parse_config(json.dumps({"enabled": True, "port": 51717, "token": "abc"})) == DrawflowConnection(51717, "abc")
    assert parse_config(json.dumps({"enabled": False, "port": 51717, "token": "abc"})) is None
    assert parse_config(json.dumps({"enabled": True, "port": 51717, "token": ""})) is None
    assert parse_config("not json") is None


def test_run_feature_sends_hello_then_command(monkeypatch):
    client, socket = make_client(monkeypatch, [{"type": "welcome", "version": 1, "locked": False}, None])
    socket.replies[1] = {"type": "result", "id": "", "ok": True, "data": {}}

    def recv_with_id() -> str:
        reply = socket.replies.pop(0)
        if reply["type"] == "result":
            reply["id"] = socket.sent[-1]["id"]
        return json.dumps(reply)

    socket.recv = recv_with_id
    client.run_feature("dwg-parts", {"files": ["C:\\Plans\\a.dwg"]})
    assert socket.sent[0]["type"] == "hello" and socket.sent[0]["version"] == 1
    assert socket.sent[1]["command"] == "feature.run"
    assert socket.sent[1]["args"] == {"moduleId": "dwg-parts", "inputs": {"files": ["C:\\Plans\\a.dwg"]}}
    assert socket.closed


def test_locked_app_is_reported(monkeypatch):
    client, _ = make_client(monkeypatch, [{"type": "welcome", "version": 1, "locked": True}])
    with pytest.raises(DrawflowError, match="verrouillée"):
        client.run_feature("dwg-parts", {})


def test_bad_token_is_reported(monkeypatch):
    client, _ = make_client(monkeypatch, [{"type": "error", "message": "Jeton invalide."}])
    with pytest.raises(DrawflowError, match="Jeton invalide"):
        client.run_feature("dwg-parts", {})


def test_missing_config_is_explained():
    client = DrawflowClient(None)
    with pytest.raises(DrawflowError, match="API locale"):
        client.command("app.state", {})
