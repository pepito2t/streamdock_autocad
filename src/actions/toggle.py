from typing import Any

from src.action_base import AutocadAction
from src.toggles import ToggleSpec, get_toggle

STATE_OFF = 0
STATE_ON = 1


class ToggleAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.start_polling()

    @property
    def spec(self) -> ToggleSpec:
        return get_toggle(self.settings.get("variable"))

    def on_key_up(self, payload: dict) -> None:
        self.perform(self._flip)

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        if snapshot is None or self.spec.variable not in snapshot:
            self.update_state(STATE_OFF)
            return
        self.update_state(STATE_ON if self.spec.is_on(snapshot[self.spec.variable]) else STATE_OFF)

    def _flip(self) -> None:
        spec = self.spec
        current = self.bridge.get_var(spec.variable)
        new_value = spec.toggled_value(current)
        self.bridge.set_var(spec.variable, new_value)
        self.update_state(STATE_ON if spec.is_on(new_value) else STATE_OFF)
