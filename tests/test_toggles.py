from src.toggles import TOGGLES, get_toggle


def test_boolean_toggle():
    ortho = TOGGLES["ORTHOMODE"]
    assert ortho.is_on(1) and not ortho.is_on(0)
    assert ortho.toggled_value(0) == 1 and ortho.toggled_value(1) == 0


def test_osmode_uses_suppression_bit():
    osnap = TOGGLES["OSMODE"]
    assert osnap.is_on(4133)
    assert not osnap.is_on(4133 | 16384)
    assert osnap.toggled_value(4133) == 4133 | 16384
    assert osnap.toggled_value(4133 | 16384) == 4133


def test_unknown_toggle_falls_back_to_ortho():
    assert get_toggle("NOPE").variable == "ORTHOMODE"
    assert get_toggle(None).variable == "ORTHOMODE"
