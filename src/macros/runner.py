from pathlib import Path
from typing import Callable

from src.bridge.autocad_bridge import AutocadBridge
from src.macros.macro import Macro

COMMAND_TERMINATOR = "\n"
LISP_STEP_PREFIX = "@lisp"

LispResolver = Callable[[str], Path]


def lisp_load_expression(path: Path) -> str:
    escaped = path.as_posix().replace("\\", "/").replace('"', '\\"')
    return f'(load "{escaped}")'


def expand_step(step: str, resolve_lisp: LispResolver) -> str:
    head, _, rest = step.strip().partition(" ")
    if head != LISP_STEP_PREFIX:
        return step
    return lisp_load_expression(resolve_lisp(rest.strip()))


def macro_command_text(macro: Macro, resolve_lisp: LispResolver) -> str:
    return "".join(expand_step(step, resolve_lisp) + COMMAND_TERMINATOR for step in macro.steps)


def steps_to_command_text(steps: tuple[str, ...] | list[str]) -> str:
    return "".join(step + COMMAND_TERMINATOR for step in steps)


def run_macro(bridge: AutocadBridge, macro: Macro, resolve_lisp: LispResolver) -> None:
    bridge.run_command(macro_command_text(macro, resolve_lisp))
