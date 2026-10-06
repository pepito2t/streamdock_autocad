from pathlib import Path, PureWindowsPath
from typing import Any

from src.action_base import AutocadAction
from src.bridge.autocad_bridge import AutocadError

NO_PAGE_SETUP = "aucune mise en page configurée sur cette touche"
NO_OUTPUT_FOLDER = "choisissez un dossier de sortie pour le PDF"
UNSAVED_DRAWING = "enregistrez le dessin avant d'exporter en PDF (le nom du fichier en dépend)"
MODE_DEVICE = "device"
MODE_PDF = "pdf"
PDF_SUFFIX = ".pdf"


def pdf_target(drawing_path: str | None, output_folder: str) -> Path:
    if not drawing_path:
        raise AutocadError(UNSAVED_DRAWING)
    if not output_folder.strip():
        raise AutocadError(NO_OUTPUT_FOLDER)
    return Path(output_folder) / (PureWindowsPath(drawing_path).stem + PDF_SUFFIX)


class PlotAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)

    @property
    def page_setup(self) -> str:
        return str(self.settings.get("page_setup", "")).strip()

    def on_key_up(self, payload: dict) -> None:
        self.perform(self._plot)

    def on_property_inspector_did_appear(self, data: dict) -> None:
        super().on_property_inspector_did_appear(data)
        self._send_page_setups()

    def on_send_to_plugin(self, payload: dict) -> None:
        if payload.get("command") == "page_setups":
            self._send_page_setups()

    def _plot(self) -> None:
        if not self.page_setup:
            raise AutocadError(NO_PAGE_SETUP)
        pdf_path = None
        if self.settings.get("mode", MODE_DEVICE) == MODE_PDF:
            target = pdf_target(self.bridge.drawing_path(), str(self.settings.get("output_folder", "")))
            pdf_path = str(target)
        self.bridge.plot(self.page_setup, pdf_path)

    def _send_page_setups(self) -> None:
        try:
            setups = self.bridge.list_page_setups()
        except AutocadError:
            setups = []
        self.send_to_property_inspector({"event": "page_setups", "page_setups": setups})
