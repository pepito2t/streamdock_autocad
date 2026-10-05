from src.actions.layer import LayerAction
from src.actions.macro import MacroAction
from src.actions.status import StatusAction
from src.actions.toggle import ToggleAction
from src.macros.preset_store import PresetStore

MACRO_UUID = "com.tmbk.streamdock.autocad.macro"


def make_macro_action(plugin, preset_dirs, settings):
    action = MacroAction(MACRO_UUID, "ctx-macro", settings, plugin)
    action.store = PresetStore(*preset_dirs)
    return action


def test_macro_preset_is_sent_to_autocad(bridge, plugin, preset_dirs):
    action = make_macro_action(plugin, preset_dirs, {"mode": "preset", "preset": "zoom"})
    action.on_key_up({})
    assert bridge.sent == ["_.ZOOM _E\n"]
    assert plugin.ws.events("showOk")


def test_macro_custom_steps(bridge, plugin, preset_dirs):
    action = make_macro_action(plugin, preset_dirs, {"mode": "custom", "steps": "_.LINE 0,0 1,1\n"})
    action.on_key_up({})
    assert bridge.sent == ["_.LINE 0,0 1,1\n\n"]


def test_macro_without_preset_alerts(bridge, plugin, preset_dirs):
    action = make_macro_action(plugin, preset_dirs, {"mode": "preset"})
    action.on_key_up({})
    assert bridge.sent == []
    assert plugin.ws.events("showAlert")


def test_macro_alerts_when_autocad_is_closed(bridge, plugin, preset_dirs):
    bridge.running = False
    action = make_macro_action(plugin, preset_dirs, {"mode": "preset", "preset": "zoom"})
    action.on_key_up({})
    assert plugin.ws.events("showAlert") and not plugin.ws.events("showOk")


def test_macro_save_from_property_inspector(bridge, plugin, preset_dirs):
    action = make_macro_action(plugin, preset_dirs, {})
    action.on_send_to_plugin({"command": "save", "macro": {"name": "Mien", "steps": "_.CIRCLE"}})
    sent = plugin.ws.events("sendToPropertyInspector")[-1]["payload"]
    assert sent["event"] == "presets"
    assert {preset["id"] for preset in sent["presets"]} == {"zoom", "mien"}


def test_macro_invalid_save_reports_error(bridge, plugin, preset_dirs):
    action = make_macro_action(plugin, preset_dirs, {})
    action.on_send_to_plugin({"command": "save", "macro": {"name": "", "steps": ""}})
    payloads = [message["payload"] for message in plugin.ws.events("sendToPropertyInspector")]
    assert payloads[0]["event"] == "error"
    assert payloads[-1]["event"] == "presets"


def test_toggle_flips_and_updates_state(bridge, plugin):
    action = ToggleAction("x.toggle", "ctx-toggle", {"variable": "ORTHOMODE"}, plugin)
    action.on_key_up({})
    assert bridge.vars["ORTHOMODE"] == 1
    assert plugin.ws.events("setState")[-1]["payload"]["state"] == 1
    action.on_key_up({})
    assert bridge.vars["ORTHOMODE"] == 0


def test_toggle_polls_autocad_state(bridge, plugin):
    bridge.vars["ORTHOMODE"] = 1
    ToggleAction("x.toggle", "ctx-toggle", {"variable": "ORTHOMODE"}, plugin)
    plugin.timer.fire_all()
    assert plugin.ws.events("setState")[-1]["payload"]["state"] == 1


def test_layer_activates_and_creates_layer(bridge, plugin):
    action = LayerAction("x.layer", "ctx-layer", {"layer": "Murs"}, plugin)
    action.on_key_up({})
    assert "Murs" in bridge.layers
    assert bridge.vars["CLAYER"] == "Murs"
    plugin.timer.fire_all()
    assert plugin.ws.events("setTitle")[-1]["payload"]["title"] == "Murs"
    assert plugin.ws.events("setState")[-1]["payload"]["state"] == 1


def test_layer_shows_disconnected_title(bridge, plugin):
    bridge.running = False
    LayerAction("x.layer", "ctx-layer", {"layer": "Murs"}, plugin)
    plugin.timer.fire_all()
    assert plugin.ws.events("setTitle")[-1]["payload"]["title"] == "AutoCAD ?"


def test_status_shows_drawing_name(bridge, plugin):
    StatusAction("x.status", "ctx-status", {"field": "drawing"}, plugin)
    plugin.timer.fire_all()
    assert plugin.ws.events("setTitle")[-1]["payload"]["title"] == "Drawing1"


def test_status_title_only_sent_on_change(bridge, plugin):
    StatusAction("x.status", "ctx-status", {"field": "layer"}, plugin)
    plugin.timer.fire_all()
    plugin.timer.fire_all()
    assert len(plugin.ws.events("setTitle")) == 1


def test_poll_survives_bridge_exceptions(bridge, plugin):
    action = StatusAction("x.status", "ctx-status", {"field": "layer"}, plugin)
    bridge.get_vars = lambda names: (_ for _ in ()).throw(RuntimeError("boom"))
    action._poll_safely()
