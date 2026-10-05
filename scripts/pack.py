"""Packs the built plugin as the zip Drawflow downloads and unpacks into Stream Dock."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "com.tmbk.streamdock.autocad.sdPlugin"
PLUGIN_FOLDER = ROOT / PLUGIN_NAME
OUTPUT = ROOT / "dist" / f"{PLUGIN_NAME}.zip"
REQUIRED = ("manifest.json", "plugin.exe")
EXCLUDED_PARTS = {"logs", "__pycache__"}


def main() -> None:
    missing = [name for name in REQUIRED if not (PLUGIN_FOLDER / name).is_file()]
    if missing:
        raise SystemExit(f"Plugin incomplet, lancez d'abord scripts/build.ps1 : {', '.join(missing)}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PLUGIN_FOLDER.rglob("*")):
            relative = path.relative_to(PLUGIN_FOLDER)
            if path.is_file() and not EXCLUDED_PARTS.intersection(relative.parts):
                archive.write(path, f"{PLUGIN_NAME}/{relative.as_posix()}")
    sys.stdout.write(f"{OUTPUT}\n")


if __name__ == "__main__":
    main()
