from dataclasses import dataclass
from typing import Any

OSNAP_SUPPRESSED_BIT = 16384


@dataclass(frozen=True)
class ToggleSpec:
    variable: str
    label: str
    mask: int | None = None
    inverted: bool = False

    def is_on(self, value: Any) -> bool:
        number = int(value)
        active = bool(number & self.mask) if self.mask else number != 0
        return not active if self.inverted else active

    def toggled_value(self, value: Any) -> int:
        number = int(value)
        if self.mask:
            return number ^ self.mask
        return 0 if number else 1


TOGGLES: dict[str, ToggleSpec] = {
    "ORTHOMODE": ToggleSpec("ORTHOMODE", "Ortho"),
    "SNAPMODE": ToggleSpec("SNAPMODE", "Accrochage grille"),
    "GRIDMODE": ToggleSpec("GRIDMODE", "Grille"),
    "LWDISPLAY": ToggleSpec("LWDISPLAY", "Épaisseurs"),
    "OSMODE": ToggleSpec("OSMODE", "Accrochage objets", mask=OSNAP_SUPPRESSED_BIT, inverted=True),
}
DEFAULT_TOGGLE = "ORTHOMODE"


def get_toggle(name: str | None) -> ToggleSpec:
    return TOGGLES.get((name or DEFAULT_TOGGLE).upper(), TOGGLES[DEFAULT_TOGGLE])
