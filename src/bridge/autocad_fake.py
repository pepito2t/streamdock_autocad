from typing import Any

from src.bridge.autocad_bridge import AutocadError, AutocadNotRunning
from src.core.logger import Logger

DEFAULT_VARS: dict[str, Any] = {
    "CLAYER": "0",
    "ORTHOMODE": 0,
    "SNAPMODE": 0,
    "GRIDMODE": 0,
    "OSMODE": 4133,
    "LWDISPLAY": 0,
    "DWGNAME": "Drawing1.dwg",
    "DWGPREFIX": "C:\\Plans\\",
    "DWGTITLED": 1,
}


class FakeAutocadBridge:
    def __init__(self, running: bool = True) -> None:
        self.running = running
        self.vars: dict[str, Any] = dict(DEFAULT_VARS)
        self.layers: set[str] = {"0"}
        self.sent: list[str] = []
        self.prompts: list[str] = []
        self.blocks: list[str] = ["Porte", "Fenetre"]
        self.page_setups: list[str] = ["A3 PDF", "A1 Traceur"]
        self.plots: list[tuple[str, str | None]] = []

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

    def list_blocks(self) -> list[str]:
        self._check_running()
        return sorted(self.blocks, key=str.lower)

    def list_page_setups(self) -> list[str]:
        self._check_running()
        return sorted(self.page_setups, key=str.lower)

    def plot(self, page_setup: str, pdf_path: str | None) -> None:
        self._check_running()
        if page_setup not in self.page_setups:
            raise AutocadError(f"mise en page introuvable : {page_setup}")
        self.plots.append((page_setup, pdf_path))

    def drawing_path(self) -> str | None:
        self._check_running()
        if not self.vars["DWGTITLED"]:
            return None
        return str(self.vars["DWGPREFIX"]) + str(self.vars["DWGNAME"])

    def reset(self) -> None:
        pass
