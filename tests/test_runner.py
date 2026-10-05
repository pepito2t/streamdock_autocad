from pathlib import Path

import pytest

from src.macros.macro import Macro
from src.macros.preset_store import LispNotFound, PresetStore
from src.macros.runner import expand_step, lisp_load_expression, macro_command_text


def test_lisp_load_uses_forward_slashes_and_escapes_quotes():
    assert lisp_load_expression(Path('C:\\Users\\t\\my "lisp"\\cube.lsp')) == '(load "C:/Users/t/my \\"lisp\\"/cube.lsp")'


def test_plain_steps_are_untouched():
    assert expand_step("_.LINE 0,0 1,1", lambda name: Path("/x")) == "_.LINE 0,0 1,1"


def test_macro_command_text_expands_lisp_steps():
    macro = Macro(id="m", name="m", steps=("@lisp a.lsp", "(c:a)"))
    assert macro_command_text(macro, lambda name: Path("/lisp") / name) == '(load "/lisp/a.lsp")\n(c:a)\n'


def test_resolve_lisp_prefers_user_file(preset_dirs):
    bundled, user = preset_dirs
    (user / "lisp").mkdir(parents=True)
    (user / "lisp" / "cube.lsp").write_text("(princ)", encoding="utf-8")
    assert PresetStore(bundled, user).resolve_lisp("cube.lsp") == user / "lisp" / "cube.lsp"


@pytest.mark.parametrize("name", ["../cube.lsp", "sub/cube.lsp", "cube.txt", "missing.lsp"])
def test_resolve_lisp_rejects_bad_names(preset_dirs, name):
    with pytest.raises(LispNotFound):
        PresetStore(*preset_dirs).resolve_lisp(name)
