from typing import Any

from src.action_base import DISCONNECTED_TITLE, AutocadAction
from src.dials import DIAL_TITLE_LENGTH, DialSpec, get_dial


class DialAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.start_polling()

    @property
    def spec(self) -> DialSpec:
        return get_dial(self.settings.get("function"))

    def on_dial_rotate(self, payload: dict) -> None:
        ticks = int(payload.get("ticks", 1) or 1)
        self.perform(lambda: self.spec.rotate(self.bridge, ticks))

    def on_dial_down(self, payload: dict) -> None:
        self.perform(lambda: self.spec.press(self.bridge))

    def on_key_up(self, payload: dict) -> None:
        self.on_dial_down(payload)

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        if snapshot is None:
            self.update_title(DISCONNECTED_TITLE)
            return
        self.update_title(self.spec.title(snapshot)[:DIAL_TITLE_LENGTH])
