from dataclasses import dataclass
from typing import Any, Callable

from src.bridge.autocad_bridge import AutocadBridge

ZOOM_IN_FACTOR = "1.2x"
ZOOM_OUT_FACTOR = "0.8x"
DIAL_TITLE_LENGTH = 10


def _repeat_command(bridge: AutocadBridge, command: str, times: int) -> None:
    bridge.run_command("".join(f"{command}\n" for _ in range(times)))


def zoom_rotate(bridge: AutocadBridge, ticks: int) -> None:
    factor = ZOOM_IN_FACTOR if ticks > 0 else ZOOM_OUT_FACTOR
    _repeat_command(bridge, f"_.ZOOM {factor}", abs(ticks))


def zoom_press(bridge: AutocadBridge) -> None:
    bridge.run_command("_.ZOOM _E\n")


def layer_rotate(bridge: AutocadBridge, ticks: int) -> None:
    layers = bridge.list_layers()
    if not layers:
        return
    current = str(bridge.get_var("CLAYER")).lower()
    names = [name.lower() for name in layers]
    index = names.index(current) if current in names else 0
    bridge.set_var("CLAYER", layers[(index + ticks) % len(layers)])


def layer_press(bridge: AutocadBridge) -> None:
    bridge.set_var("CLAYER", "0")


def undo_rotate(bridge: AutocadBridge, ticks: int) -> None:
    _repeat_command(bridge, "_.REDO" if ticks > 0 else "_.U", abs(ticks))


def undo_press(bridge: AutocadBridge) -> None:
    bridge.run_command("_.REGEN\n")


@dataclass(frozen=True)
class DialSpec:
    label: str
    rotate: Callable[[AutocadBridge, int], None]
    press: Callable[[AutocadBridge], None]
    title: Callable[[dict[str, Any]], str]


DIALS: dict[str, DialSpec] = {
    "zoom": DialSpec("Zoom", zoom_rotate, zoom_press, lambda snapshot: "Zoom"),
    "layer": DialSpec("Calque", layer_rotate, layer_press, lambda snapshot: str(snapshot.get("CLAYER", ""))),
    "undo": DialSpec("Annuler / Rétablir", undo_rotate, undo_press, lambda snapshot: "Undo"),
}
DEFAULT_DIAL = "zoom"


def get_dial(name: str | None) -> DialSpec:
    return DIALS.get((name or DEFAULT_DIAL).lower(), DIALS[DEFAULT_DIAL])
