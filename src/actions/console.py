from pathlib import Path
from typing import Any, Callable

from src.action_base import AutocadAction
from src.console.instance import SingleInstance
from src.console.launcher import show_console
from src.core.logger import Logger

TITLE = "Console"
MAX_DISPLAYED_ERRORS = 99
REFRESH_INTERVAL_MS = 1000


def console_title(unseen_errors: int) -> str:
    if unseen_errors <= 0:
        return TITLE
    count = f"{MAX_DISPLAYED_ERRORS}+" if unseen_errors > MAX_DISPLAYED_ERRORS else str(unseen_errors)
    label = "erreur" if unseen_errors == 1 else "erreurs"
    return f"{TITLE}\n{count} {label}"


def write_memory_snapshot(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(line + "\n" for line in Logger.memory().lines()), encoding="utf-8")
    return target


class ConsoleAction(AutocadAction):
    def __init__(self, action: str, context: str, settings: dict, plugin: Any) -> None:
        super().__init__(action, context, settings, plugin)
        self.launch: Callable[[Path], None] = show_console
        self.update_title(console_title(Logger.memory().unseen_errors()))
        self.plugin.timer.set_interval(self._timer_id(), REFRESH_INTERVAL_MS, self.refresh_title)

    def on_key_up(self, payload: dict) -> None:
        self.perform(self._open_console)

    def refresh_title(self) -> None:
        self.update_title(console_title(Logger.memory().unseen_errors()))

    def _open_console(self) -> None:
        log_file = Logger.log_file() or write_memory_snapshot(SingleInstance().snapshot_path)
        self.launch(log_file)
        Logger.memory().mark_errors_seen()
        self.refresh_title()
