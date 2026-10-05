import pytest

from src.macros.macro import InvalidMacro, Macro, macro_from_dict, parse_steps, slugify
from src.macros.runner import steps_to_command_text


def test_steps_become_newline_terminated_text():
    assert steps_to_command_text(["_.LINE 0,0 10,10", "", "_.ZOOM _E"]) == "_.LINE 0,0 10,10\n\n_.ZOOM _E\n"


def test_parse_steps_accepts_multiline_string():
    assert parse_steps("_.-LAYER _M Cube\n\n_.BOX") == ("_.-LAYER _M Cube", "", "_.BOX")


def test_parse_steps_rejects_empty_macro():
    with pytest.raises(InvalidMacro):
        parse_steps("\n\n")


def test_slugify_handles_accents_and_spaces():
    assert slugify("  Zoom étendu !") == "zoom-tendu"


def test_slugify_rejects_symbols_only():
    with pytest.raises(InvalidMacro):
        slugify("***")


def test_macro_from_dict_requires_name():
    with pytest.raises(InvalidMacro):
        macro_from_dict({"name": " ", "steps": ["x"]})


def test_macro_to_dict_roundtrip():
    macro = Macro(id="cube", name="Cube", steps=("_.BOX",), description="d", builtin=True)
    assert macro.to_dict() == {"id": "cube", "name": "Cube", "description": "d", "steps": ["_.BOX"], "builtin": True}
