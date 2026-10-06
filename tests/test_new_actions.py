import pytest

from src.actions.block import BlockAction, insert_command
from src.actions.drawflow import DrawflowAction
from src.actions.plot import PlotAction, pdf_target
from src.bridge.autocad_bridge import AutocadError
from src.drawflow_client import DrawflowError, DrawflowModule


class FakeDrawflow:
    def __init__(self, modules=None, error: DrawflowError | None = None) -> None:
        self.modules = modules or [DrawflowModule("dwg-parts", "Liste de pièces")]
        self.error = error
        self.runs: list[tuple[str, dict]] = []

    def run_feature(self, module_id: str, inputs: dict) -> None:
        if self.error:
            raise self.error
        self.runs.append((module_id, inputs))

    def list_modules(self) -> list[DrawflowModule]:
        if self.error:
            raise self.error
        return self.modules


def make_drawflow(plugin, settings, client=None) -> tuple[DrawflowAction, FakeDrawflow]:
    action = DrawflowAction("x.drawflow", "ctx-df", settings, plugin)
    action.client = client or FakeDrawflow()
    return action, action.client


def test_drawflow_sends_saved_drawing_with_project_name(bridge, plugin):
    action, client = make_drawflow(plugin, {})
    action.on_key_up({})
    assert client.runs == [("dwg-parts", {"files": ["C:\\Plans\\Drawing1.dwg"], "project": "Drawing1"})]
    assert plugin.ws.events("showOk")


def test_drawflow_respects_module_and_project_settings(bridge, plugin):
    action, client = make_drawflow(plugin, {"module": "pdf-report", "project_from_name": False})
    action.on_key_up({})
    assert client.runs == [("pdf-report", {"files": ["C:\\Plans\\Drawing1.dwg"]})]


def test_drawflow_refuses_unsaved_drawing(bridge, plugin):
    bridge.vars["DWGTITLED"] = 0
    action, client = make_drawflow(plugin, {})
    action.on_key_up({})
    assert client.runs == []
    assert "enregistr" in plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["message"]


def test_drawflow_offline_is_reported(bridge, plugin):
    action, _ = make_drawflow(plugin, {}, FakeDrawflow(error=DrawflowError("Drawflow n'est pas joignable")))
    action.on_key_up({})
    assert "joignable" in plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["message"]


def test_drawflow_lists_modules_for_property_inspector(bridge, plugin):
    action, _ = make_drawflow(plugin, {})
    action.on_property_inspector_did_appear({})
    payload = plugin.ws.events("sendToPropertyInspector")[-1]["payload"]
    assert payload == {"event": "modules", "modules": [{"id": "dwg-parts", "name": "Liste de pièces"}], "message": ""}


def test_drawflow_title_is_drawing_name(bridge, plugin):
    make_drawflow(plugin, {})
    plugin.timer.fire_all()
    assert plugin.ws.events("setTitle")[-1]["payload"]["title"] == "Drawing1"


def test_insert_command_formats_options():
    assert insert_command("Porte", 1.0, 0.0) == '_.-INSERT "Porte" _S 1 _R 0\n'
    assert insert_command("Porte", 0.5, 90.0) == '_.-INSERT "Porte" _S 0.5 _R 90\n'
    assert insert_command("Porte", None, None) == '_.-INSERT "Porte"\n'


def test_block_inserts_with_fixed_scale(bridge, plugin):
    BlockAction("x.block", "ctx-b", {"block": "Porte", "scale": "2", "rotation": "45"}, plugin).on_key_up({})
    assert bridge.sent == ['_.-INSERT "Porte" _S 2 _R 45\n']


def test_block_asks_scale_when_not_fixed(bridge, plugin):
    BlockAction("x.block", "ctx-b", {"block": "Porte", "fixed": False}, plugin).on_key_up({})
    assert bridge.sent == ['_.-INSERT "Porte"\n']


def test_block_without_name_reports_error(bridge, plugin):
    BlockAction("x.block", "ctx-b", {}, plugin).on_key_up({})
    assert bridge.sent == []
    assert "bloc" in plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["message"]


def test_block_lists_blocks(bridge, plugin):
    BlockAction("x.block", "ctx-b", {}, plugin).on_property_inspector_did_appear({})
    assert plugin.ws.events("sendToPropertyInspector")[-1]["payload"] == {"event": "blocks", "blocks": ["Fenetre", "Porte"]}


def test_plot_to_device_with_page_setup(bridge, plugin):
    PlotAction("x.plot", "ctx-p", {"page_setup": "A3 PDF"}, plugin).on_key_up({})
    assert bridge.plots == [("A3 PDF", None)]


def test_plot_to_pdf_names_file_after_drawing(bridge, plugin):
    settings = {"page_setup": "A3 PDF", "mode": "pdf", "output_folder": "C:\\Sorties"}
    PlotAction("x.plot", "ctx-p", settings, plugin).on_key_up({})
    assert bridge.plots == [("A3 PDF", str(pdf_target("C:\\Plans\\Drawing1.dwg", "C:\\Sorties")))]
    assert bridge.plots[0][1].endswith("Drawing1.pdf")


def test_plot_unknown_page_setup_reports_error(bridge, plugin):
    PlotAction("x.plot", "ctx-p", {"page_setup": "Nope"}, plugin).on_key_up({})
    assert bridge.plots == []
    assert "Nope" in plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["message"]


def test_plot_pdf_requires_folder_and_saved_drawing():
    with pytest.raises(AutocadError, match="dossier"):
        pdf_target("C:\\Plans\\a.dwg", " ")
    with pytest.raises(AutocadError, match="enregistrez"):
        pdf_target(None, "C:\\Sorties")


def test_plot_lists_page_setups(bridge, plugin):
    PlotAction("x.plot", "ctx-p", {}, plugin).on_send_to_plugin({"command": "page_setups"})
    assert plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["page_setups"] == ["A1 Traceur", "A3 PDF"]
