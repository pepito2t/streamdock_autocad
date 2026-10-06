from typing import Any

from src.action_base import AutocadAction
from src.bridge.autocad_bridge import AutocadError

NO_BLOCK = "aucun bloc configuré sur cette touche"
DEFAULT_SCALE = 1.0
DEFAULT_ROTATION = 0.0


def insert_command(block: str, scale: float | None, rotation: float | None) -> str:
    options = ""
    if scale is not None:
        options += f" _S {scale:g}"
    if rotation is not None:
        options += f" _R {rotation:g}"
    return f'_.-INSERT "{block}"{options}\n'


class BlockAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)

    @property
    def block_name(self) -> str:
        return str(self.settings.get("block", "")).strip()

    def on_key_up(self, payload: dict) -> None:
        self.perform(self._insert)

    def on_property_inspector_did_appear(self, data: dict) -> None:
        super().on_property_inspector_did_appear(data)
        self._send_blocks()

    def on_send_to_plugin(self, payload: dict) -> None:
        if payload.get("command") == "blocks":
            self._send_blocks()

    def _insert(self) -> None:
        if not self.block_name:
            raise AutocadError(NO_BLOCK)
        fixed = self.settings.get("fixed", True)
        scale = _number(self.settings.get("scale"), DEFAULT_SCALE) if fixed else None
        rotation = _number(self.settings.get("rotation"), DEFAULT_ROTATION) if fixed else None
        self.bridge.run_command(insert_command(self.block_name, scale, rotation))

    def _send_blocks(self) -> None:
        try:
            blocks = self.bridge.list_blocks()
        except AutocadError:
            blocks = []
        self.send_to_property_inspector({"event": "blocks", "blocks": blocks})


def _number(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
