import os
import sys
from pathlib import Path

PLUGIN_DIR_NAME = "com.tmbk.streamdock.autocad.sdPlugin"
USER_DATA_SUBDIR = Path("tmbk") / "streamdock-autocad"


def plugin_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent / PLUGIN_DIR_NAME


def bundled_presets_dir() -> Path:
    return plugin_dir() / "presets"


def user_presets_dir() -> Path:
    override = os.environ.get("STREAMDOCK_AUTOCAD_USER_DIR")
    if override:
        return Path(override) / "presets"
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / ".config"
    return base / USER_DATA_SUBDIR / "presets"
