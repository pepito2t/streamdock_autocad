from typing import Any

from src.bridge.autocad_bridge import AutocadNotRunning
from src.core.logger import Logger

DEFAULT_VARS: dict[str, Any] = {
    "CLAYER": "0",
    "ORTHOMODE": 0,
    "SNAPMODE": 0,
    "GRIDMODE": 0,
    "OSMODE": 4133,
    "LWDISPLAY": 0,
    "DWGNAME": "Drawing1.dwg",
}


class FakeAutocadBridge:
    def __init__(self, running: bool = True) -> None:
        self.running = running
        self.vars: dict[str, Any] = dict(DEFAULT_VARS)
        self.layers: set[str] = {"0"}
        self.sent: list[str] = []
        self.prompts: list[str] = []

    def _check_running(self) -> None:
        if not self.running:
            raise AutocadNotRunning("fake AutoCAD is not running")

    def is_connected(self) -> bool:
        return self.running

    def run_command(self, text: str) -> None:
        self._check_running()
        self.sent.append(text)
        Logger.info(f"[FakeAutocad] SendCommand: {text!r}")

    def get_var(self, name: str) -> Any:
        self._check_running()
        return self.vars[name.upper()]

    def set_var(self, name: str, value: Any) -> None:
        self._check_running()
        self.vars[name.upper()] = value

    def get_vars(self, names: list[str]) -> dict[str, Any]:
        return {name: self.get_var(name) for name in names}

    def ensure_layer(self, name: str) -> None:
        self._check_running()
        self.layers.add(name)

    def list_layers(self) -> list[str]:
        self._check_running()
        return sorted(self.layers, key=str.lower)

    def prompt(self, message: str) -> None:
        self._check_running()
        self.prompts.append(message)

    def reset(self) -> None:
        pass
