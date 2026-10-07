import argparse
import sys
from pathlib import Path

from src.console.instance import SingleInstance

EXIT_OK = 0
EXIT_NO_DISPLAY = 3
EXIT_NO_TKINTER = 4


def parse_console_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="plugin --console", description="Fenêtre du journal du plugin AutoCAD")
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--smoke", action="store_true", help="construit la fenêtre puis la ferme (CI)")
    return parser.parse_args(argv)


def report(message: str) -> None:
    # The frozen plugin has no console: stderr only exists when a parent process captures it.
    if sys.stderr is not None:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()


def run_console(argv: list[str]) -> int:
    args = parse_console_args(argv)
    if args.smoke:
        return open_window(args.log_path, None, smoke=True)
    instance = SingleInstance()
    try:
        acquired = instance.acquire()
    except OSError as error:
        report(f"Verrou de la console indisponible, fenêtre ouverte sans contrôle d'unicité : {error}")
        return open_window(args.log_path, None)
    if not acquired:
        instance.request_focus()
        return EXIT_OK
    try:
        return open_window(args.log_path, instance)
    finally:
        instance.release()


def open_window(log_path: Path, instance: SingleInstance | None, smoke: bool = False) -> int:
    try:
        from src.console import window
    except ImportError as error:
        report(f"tkinter indisponible : {error}")
        return EXIT_NO_TKINTER
    try:
        line_count = window.run(log_path, instance, smoke)
    except window.NoDisplay as error:
        report(f"Aucun affichage disponible, console non ouverte : {error}")
        return EXIT_NO_DISPLAY
    if smoke:
        report(f"console ok ({line_count} lignes)")
    return EXIT_OK
