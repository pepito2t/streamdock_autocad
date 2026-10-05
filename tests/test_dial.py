from src.actions.dial import DialAction
from src.dials import get_dial


def test_zoom_rotate_repeats_per_tick(bridge, plugin):
    action = DialAction("x.dial", "ctx-dial", {"function": "zoom"}, plugin)
    action.on_dial_rotate({"ticks": 2})
    action.on_dial_rotate({"ticks": -1})
    assert bridge.sent == ["_.ZOOM 1.2x\n_.ZOOM 1.2x\n", "_.ZOOM 0.8x\n"]


def test_zoom_press_is_zoom_extents(bridge, plugin):
    DialAction("x.dial", "ctx-dial", {"function": "zoom"}, plugin).on_dial_down({})
    assert bridge.sent == ["_.ZOOM _E\n"]


def test_layer_rotate_cycles_through_layers(bridge, plugin):
    bridge.layers.update({"Cotes", "Murs"})
    bridge.vars["CLAYER"] = "Murs"
    action = DialAction("x.dial", "ctx-dial", {"function": "layer"}, plugin)
    action.on_dial_rotate({"ticks": 1})
    assert bridge.vars["CLAYER"] == "0"
    action.on_dial_rotate({"ticks": -1})
    assert bridge.vars["CLAYER"] == "Murs"


def test_layer_press_returns_to_layer_zero(bridge, plugin):
    bridge.vars["CLAYER"] = "Murs"
    DialAction("x.dial", "ctx-dial", {"function": "layer"}, plugin).on_dial_down({})
    assert bridge.vars["CLAYER"] == "0"


def test_undo_rotate_sends_undo_or_redo(bridge, plugin):
    action = DialAction("x.dial", "ctx-dial", {"function": "undo"}, plugin)
    action.on_dial_rotate({"ticks": -2})
    action.on_dial_rotate({"ticks": 1})
    assert bridge.sent == ["_.U\n_.U\n", "_.REDO\n"]


def test_dial_title_shows_current_layer(bridge, plugin):
    bridge.vars["CLAYER"] = "Murs"
    DialAction("x.dial", "ctx-dial", {"function": "layer"}, plugin)
    plugin.timer.fire_all()
    assert plugin.ws.events("setTitle")[-1]["payload"]["title"] == "Murs"


def test_dial_error_when_autocad_closed(bridge, plugin):
    bridge.running = False
    DialAction("x.dial", "ctx-dial", {"function": "zoom"}, plugin).on_dial_rotate({"ticks": 1})
    assert plugin.ws.events("showAlert")


def test_unknown_function_falls_back_to_zoom():
    assert get_dial("nope").label == "Zoom"
