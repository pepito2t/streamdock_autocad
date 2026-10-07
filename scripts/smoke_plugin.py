"""Checks that the frozen plugin starts and that its log console opens, or exits cleanly without a display."""

import subprocess
import sys
import tempfile
from pathlib import Path

ARGPARSE_USAGE_EXIT_CODE = 2
CONSOLE_OK_EXIT_CODE = 0
CONSOLE_NO_DISPLAY_EXIT_CODE = 3
TIMEOUT_S = 30
SAMPLE_LOG_LINE = "2026-01-01 00:00:00,000 - StreamDock - ERROR - smoke test\n"


def check_plugin_start(path: Path) -> None:
    result = subprocess.run([str(path)], capture_output=True, text=True, timeout=TIMEOUT_S)
    if result.returncode != ARGPARSE_USAGE_EXIT_CODE or "-pluginUUID" not in result.stderr:
        raise SystemExit(f"Démarrage anormal (code {result.returncode}) :\n{result.stdout}\n{result.stderr}")


def check_console(path: Path) -> str:
    with tempfile.TemporaryDirectory() as folder:
        log = Path(folder) / "plugin.log"
        log.write_text(SAMPLE_LOG_LINE, encoding="utf-8")
        command = [str(path), "--console", str(log), "--smoke"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_S)
    if result.returncode == CONSOLE_OK_EXIT_CODE and "console ok (1 lignes)" in result.stderr:
        return "console ouverte et fermée"
    if result.returncode == CONSOLE_NO_DISPLAY_EXIT_CODE:
        return "console sans affichage, sortie propre"
    raise SystemExit(f"Console anormale (code {result.returncode}) :\n{result.stdout}\n{result.stderr}")


def main(executable: str) -> None:
    path = Path(executable)
    if not path.is_file():
        raise SystemExit(f"Exécutable introuvable : {path}")
    check_plugin_start(path)
    console = check_console(path)
    print(f"{path.name} démarre correctement ({path.stat().st_size // 1_000_000} MB), {console}")


if __name__ == "__main__":
    main(sys.argv[1])
