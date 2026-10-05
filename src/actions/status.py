from typing import Any, Callable

from src.action_base import DISCONNECTED_TITLE, AutocadAction
from src.toggles import TOGGLES

MAX_TITLE_LENGTH = 14


def _drawing_name(snapshot: dict[str, Any]) -> str:
    return str(snapshot.get("DWGNAME", "")).removesuffix(".dwg")


def _layer_name(snapshot: dict[str, Any]) -> str:
    return str(snapshot.get("CLAYER", ""))


def _modes(snapshot: dict[str, Any]) -> str:
    active = [spec.label for name, spec in TOGGLES.items() if name in snapshot and spec.is_on(snapshot[name])]
    return "\n".join(label[:6] for label in active) or "—"


FIELDS: dict[str, Callable[[dict[str, Any]], str]] = {
    "drawing": _drawing_name,
    "layer": _layer_name,
    "modes": _modes,
}
DEFAULT_FIELD = "layer"


class StatusAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.start_polling()

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        if snapshot is None:
            self.update_title(DISCONNECTED_TITLE)
            return
        field = FIELDS.get(str(self.settings.get("field", DEFAULT_FIELD)), FIELDS[DEFAULT_FIELD])
        self.update_title(field(snapshot)[:MAX_TITLE_LENGTH])
