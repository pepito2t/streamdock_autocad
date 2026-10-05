from typing import Any, Callable

from src.autocad_state import get_state
from src.bridge import get_bridge
from src.bridge.autocad_bridge import AutocadBridge, AutocadError
from src.core.action import Action
from src.core.logger import Logger

POLL_INTERVAL_MS = 1000
DISCONNECTED_TITLE = "AutoCAD ?"


class AutocadAction(Action):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self._last_title: str | None = None
        self._last_state: int | None = None

    @property
    def bridge(self) -> AutocadBridge:
        return get_bridge()

    def start_polling(self) -> None:
        self.plugin.timer.set_interval(self._timer_id(), POLL_INTERVAL_MS, self._poll_safely)

    def on_will_disappear(self) -> None:
        self.plugin.timer.clear_interval(self._timer_id())

    def on_did_receive_settings(self, settings: dict) -> None:
        self.settings = settings
        self._last_title = None
        self._last_state = None

    def on_application_did_launch(self, data: dict) -> None:
        self._reconnect()

    def on_application_did_terminate(self, data: dict) -> None:
        self._reconnect()

    def on_system_did_wake_up(self, data: dict) -> None:
        self._reconnect()

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        pass

    def perform(self, fn: Callable[[], None]) -> None:
        try:
            fn()
            get_state().invalidate()
            self.show_ok()
        except AutocadError as error:
            Logger.error(f"[{type(self).__name__}] {error}")
            self.show_alert()

    def update_title(self, title: str) -> None:
        if title != self._last_title:
            self._last_title = title
            self.set_title(title)

    def update_state(self, state: int) -> None:
        if state != self._last_state:
            self._last_state = state
            self.set_state(state)

    def _timer_id(self) -> str:
        return f"poll_{self.context}"

    def _poll_safely(self) -> None:
        try:
            self.refresh(get_state().snapshot())
        except Exception as error:
            Logger.error(f"[{type(self).__name__}] poll failed: {error}")

    def _reconnect(self) -> None:
        try:
            self.bridge.reset()
        except AutocadError as error:
            Logger.warning(f"[{type(self).__name__}] reset failed: {error}")
        get_state().invalidate()
