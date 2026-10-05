"""Checks that the frozen plugin starts: without arguments it must exit with argparse's usage error."""

import subprocess
import sys
from pathlib import Path

ARGPARSE_USAGE_EXIT_CODE = 2
TIMEOUT_S = 30


def main(executable: str) -> None:
    path = Path(executable)
    if not path.is_file():
        raise SystemExit(f"Exécutable introuvable : {path}")
    result = subprocess.run([str(path)], capture_output=True, text=True, timeout=TIMEOUT_S)
    if result.returncode != ARGPARSE_USAGE_EXIT_CODE or "-pluginUUID" not in result.stderr:
        raise SystemExit(f"Démarrage anormal (code {result.returncode}) :\n{result.stdout}\n{result.stderr}")
    print(f"{path.name} démarre correctement ({path.stat().st_size // 1_000_000} MB)")


if __name__ == "__main__":
    main(sys.argv[1])
