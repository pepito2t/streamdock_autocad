import os
import subprocess
import sys
from pathlib import Path

from src.console.instance import SingleInstance

CONSOLE_FLAG = "--console"
MAIN_SCRIPT = Path(__file__).resolve().parent.parent.parent / "main.py"
LAUNCH_FAILED = "Impossible d'ouvrir la console du plugin : {error}"


class ConsoleLaunchError(Exception):
    pass


def console_command(log_path: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, CONSOLE_FLAG, str(log_path)]
    return [sys.executable, str(MAIN_SCRIPT), CONSOLE_FLAG, str(log_path)]


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    # Without it, a onefile build would run inside the plugin's temporary folder, deleted when the plugin stops.
    environment["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    return environment


def _creation_flags() -> int:
    if os.name != "nt":
        return 0
    return subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP


def show_console(log_path: Path, instance: SingleInstance | None = None) -> None:
    instance = instance or SingleInstance()
    try:
        if instance.is_running():
            instance.request_focus()
            return
        subprocess.Popen(
            console_command(log_path),
            env=_child_environment(),
            creationflags=_creation_flags(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    except OSError as error:
        raise ConsoleLaunchError(LAUNCH_FAILED.format(error=error)) from error
