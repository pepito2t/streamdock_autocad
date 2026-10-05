from src.bridge.autocad_bridge import AutocadBridge
from src.macros.macro import Macro

COMMAND_TERMINATOR = "\n"


def steps_to_command_text(steps: tuple[str, ...] | list[str]) -> str:
    return "".join(step + COMMAND_TERMINATOR for step in steps)


def run_macro(bridge: AutocadBridge, macro: Macro) -> None:
    bridge.run_command(steps_to_command_text(macro.steps))
