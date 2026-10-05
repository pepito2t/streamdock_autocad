from typing import Any

from src.action_base import DISCONNECTED_TITLE, AutocadAction
from src.bridge.autocad_bridge import AutocadError

STATE_INACTIVE = 0
STATE_ACTIVE = 1
MAX_TITLE_LENGTH = 12


class LayerAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.start_polling()

    @property
    def layer_name(self) -> str:
        return str(self.settings.get("layer", "")).strip()

    def on_key_up(self, payload: dict) -> None:
        if not self.layer_name:
            self.report_error(AutocadError("aucun calque configuré sur cette touche"))
            return
        self.perform(self._activate)

    def on_property_inspector_did_appear(self, data: dict) -> None:
        super().on_property_inspector_did_appear(data)
        self._send_layers()

    def on_send_to_plugin(self, payload: dict) -> None:
        if payload.get("command") == "layers":
            self._send_layers()

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        if snapshot is None:
            self.update_title(DISCONNECTED_TITLE)
            self.update_state(STATE_INACTIVE)
            return
        current = str(snapshot.get("CLAYER", ""))
        self.update_title(current[:MAX_TITLE_LENGTH])
        is_active = current.lower() == self.layer_name.lower()
        self.update_state(STATE_ACTIVE if is_active else STATE_INACTIVE)

    def _activate(self) -> None:
        if self.settings.get("create", True):
            self.bridge.ensure_layer(self.layer_name)
        try:
            self.bridge.set_var("CLAYER", self.layer_name)
        except AutocadError as error:
            raise AutocadError(f"calque {self.layer_name!r} inaccessible : {error}") from error

    def _send_layers(self) -> None:
        try:
            layers = self.bridge.list_layers()
            current = str(self.bridge.get_var("CLAYER"))
        except AutocadError:
            layers, current = [], ""
        self.send_to_property_inspector({"event": "layers", "layers": layers, "current": current})
