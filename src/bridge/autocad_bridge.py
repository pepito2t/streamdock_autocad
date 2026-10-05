from typing import Any, Protocol


class AutocadError(Exception):
    pass


class AutocadNotRunning(AutocadError):
    pass


class AutocadBusy(AutocadError):
    pass


class AutocadBridge(Protocol):
    def is_connected(self) -> bool: ...

    def run_command(self, text: str) -> None: ...

    def get_var(self, name: str) -> Any: ...

    def set_var(self, name: str, value: Any) -> None: ...

    def get_vars(self, names: list[str]) -> dict[str, Any]: ...

    def ensure_layer(self, name: str) -> None: ...

    def list_layers(self) -> list[str]: ...

    def prompt(self, message: str) -> None: ...

    def reset(self) -> None: ...
