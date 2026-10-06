from pathlib import PureWindowsPath
from typing import Any

from src.action_base import DISCONNECTED_TITLE, AutocadAction
from src.bridge.autocad_bridge import AutocadError
from src.drawflow_client import DrawflowClient, DrawflowError

DEFAULT_MODULE = "dwg-parts"
UNSAVED_DRAWING = "Le dessin n'est pas enregistré : enregistrez-le avant de l'envoyer à Drawflow."
MAX_TITLE_LENGTH = 14


class DrawflowAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.client = DrawflowClient()
        self.start_polling()

    @property
    def module_id(self) -> str:
        return str(self.settings.get("module") or DEFAULT_MODULE)

    def on_key_up(self, payload: dict) -> None:
        self.perform(self._send_current_drawing)

    def on_property_inspector_did_appear(self, data: dict) -> None:
        super().on_property_inspector_did_appear(data)
        self._send_modules()

    def on_send_to_plugin(self, payload: dict) -> None:
        if payload.get("command") == "modules":
            self._send_modules()

    def refresh(self, snapshot: dict[str, Any] | None) -> None:
        if snapshot is None:
            self.update_title(DISCONNECTED_TITLE)
            return
        name = str(snapshot.get("DWGNAME", "")).removesuffix(".dwg")
        self.update_title(name[:MAX_TITLE_LENGTH])

    def _send_current_drawing(self) -> None:
        path = self.bridge.drawing_path()
        if not path:
            raise AutocadError(UNSAVED_DRAWING)
        self.client.run_feature(self.module_id, self._inputs_for(PureWindowsPath(path)))

    def _inputs_for(self, drawing: PureWindowsPath) -> dict[str, Any]:
        inputs: dict[str, Any] = {"files": [str(drawing)]}
        if self.settings.get("project_from_name", True):
            inputs["project"] = drawing.stem
        return inputs

    def _send_modules(self) -> None:
        try:
            modules = [{"id": module.id, "name": module.name} for module in self.client.list_modules()]
            message = ""
        except DrawflowError as error:
            modules, message = [], str(error)
        self.send_to_property_inspector({"event": "modules", "modules": modules, "message": message})
