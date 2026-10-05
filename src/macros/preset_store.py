import json
from pathlib import Path
from typing import Any

from src.core.logger import Logger
from src.macros.macro import InvalidMacro, Macro, macro_from_dict
from src.paths import bundled_presets_dir, user_presets_dir


class PresetNotFound(KeyError):
    pass


class PresetReadOnly(PermissionError):
    pass


class LispNotFound(InvalidMacro):
    pass


LISP_SUBDIR = "lisp"
LISP_SUFFIX = ".lsp"


class PresetStore:
    def __init__(self, bundled_dir: Path | None = None, user_dir: Path | None = None) -> None:
        self.bundled_dir = bundled_dir or bundled_presets_dir()
        self.user_dir = user_dir or user_presets_dir()

    def list(self) -> list[Macro]:
        macros = self._load_dir(self.bundled_dir, builtin=True)
        macros.update(self._load_dir(self.user_dir, builtin=False))
        return sorted(macros.values(), key=lambda macro: macro.name.lower())

    def get(self, macro_id: str) -> Macro:
        for macro in self.list():
            if macro.id == macro_id:
                return macro
        raise PresetNotFound(macro_id)

    def save(self, data: dict[str, Any]) -> Macro:
        macro = macro_from_dict(data)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        payload = {"name": macro.name, "description": macro.description, "steps": list(macro.steps)}
        (self.user_dir / f"{macro.id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return macro

    def delete(self, macro_id: str) -> None:
        path = self.user_dir / f"{macro_id}.json"
        if not path.exists():
            if (self.bundled_dir / f"{macro_id}.json").exists():
                raise PresetReadOnly(macro_id)
            raise PresetNotFound(macro_id)
        path.unlink()

    def resolve_lisp(self, file_name: str) -> Path:
        if Path(file_name).name != file_name or not file_name.lower().endswith(LISP_SUFFIX):
            raise LispNotFound(f"nom de fichier LISP invalide : {file_name!r}")
        for directory in (self.user_dir, self.bundled_dir):
            candidate = directory / LISP_SUBDIR / file_name
            if candidate.is_file():
                return candidate
        raise LispNotFound(f"fichier LISP introuvable : {file_name}")

    def _load_dir(self, directory: Path, builtin: bool) -> dict[str, Macro]:
        macros: dict[str, Macro] = {}
        if not directory.is_dir():
            return macros
        for path in sorted(directory.glob("*.json")):
            macro = self._load_file(path, builtin)
            if macro is not None:
                macros[macro.id] = macro
        return macros

    def _load_file(self, path: Path, builtin: bool) -> Macro | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return macro_from_dict(data, macro_id=path.stem, builtin=builtin)
        except (OSError, json.JSONDecodeError, InvalidMacro) as error:
            Logger.error(f"[PresetStore] skipping {path.name}: {error}")
            return None
