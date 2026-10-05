from typing import Any

from src.action_base import AutocadAction
from src.core.logger import Logger
from src.macros.macro import InvalidMacro, Macro, parse_steps
from src.macros.preset_store import PresetNotFound, PresetReadOnly, PresetStore
from src.macros.runner import run_macro

MODE_PRESET = "preset"
MODE_CUSTOM = "custom"


class MacroAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.store = PresetStore()

    def on_key_up(self, payload: dict) -> None:
        try:
            macro = self._resolve_macro()
        except (InvalidMacro, PresetNotFound) as error:
            Logger.error(f"[MacroAction] invalid configuration: {error}")
            self.show_alert()
            return
        self.perform(lambda: run_macro(self.bridge, macro))

    def on_property_inspector_did_appear(self, data: dict) -> None:
        self._send_presets()

    def on_send_to_plugin(self, payload: dict) -> None:
        command = payload.get("command")
        try:
            if command == "save":
                self.store.save(payload.get("macro", {}))
            elif command == "delete":
                self.store.delete(str(payload.get("id", "")))
            elif command != "list":
                return
        except (InvalidMacro, PresetNotFound, PresetReadOnly, OSError) as error:
            Logger.error(f"[MacroAction] {command} failed: {error}")
            self.send_to_property_inspector({"event": "error", "message": str(error)})
        self._send_presets()

    def _resolve_macro(self) -> Macro:
        if self.settings.get("mode", MODE_PRESET) == MODE_CUSTOM:
            steps = parse_steps(self.settings.get("steps", ""))
            return Macro(id="custom", name="custom", steps=steps)
        preset_id = self.settings.get("preset")
        if not preset_id:
            raise PresetNotFound("no preset selected")
        return self.store.get(str(preset_id))

    def _send_presets(self) -> None:
        presets = [macro.to_dict() for macro in self.store.list()]
        self.send_to_property_inspector({"event": "presets", "presets": presets})
