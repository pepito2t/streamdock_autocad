import tkinter as tk

import pytest

from src.console import window as console_window
from src.console.app import EXIT_NO_DISPLAY, EXIT_OK, run_console
from src.console.journal import LevelFilter, LogFollower

HEADER = "AutoCAD plugin v0.3.0 · Windows 11 · 2026-10-07T10:00:00+02:00"
LINES = [
    "2026-10-07 10:00:00,001 - StreamDock - INFO - keyDown",
    "2026-10-07 10:00:01,002 - StreamDock - WARNING - check failed",
    "2026-10-07 10:00:02,003 - StreamDock - ERROR - AutoCAD n'est pas ouvert",
    "Traceback (most recent call last):",
]


@pytest.fixture
def root():
    try:
        root = tk.Tk()
    except tk.TclError as error:
        pytest.skip(f"no display: {error}")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def log(tmp_path):
    path = tmp_path / "plugin.log"
    path.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    return path


def make_window(root, log) -> console_window.ConsoleWindow:
    window = console_window.ConsoleWindow(root, LogFollower(log), header=lambda: HEADER)
    window.start()
    return window


def test_window_shows_log_and_filters_levels(root, log):
    window = make_window(root, log)
    assert window.listbox.size() == len(LINES)
    window.level_filter.set(LevelFilter.ERRORS.name)
    window.render()
    assert window.listbox.get(0, tk.END) == tuple(LINES[2:])
    window.level_filter.set(LevelFilter.WARNINGS.name)
    window.render()
    assert window.listbox.size() == 3


def test_copy_selection_puts_header_and_lines_in_clipboard(root, log):
    window = make_window(root, log)
    window.listbox.selection_set(1, 2)
    window.copy_selection()
    assert root.clipboard_get() == "\n".join([HEADER, *LINES[1:3]]) + "\n"
    assert "2 ligne(s)" in window.status.get()


def test_copy_without_selection_explains(root, log):
    window = make_window(root, log)
    window.copy_selection()
    assert window.status.get() == console_window.NO_SELECTION


def test_copy_all_copies_visible_lines(root, log):
    window = make_window(root, log)
    window.level_filter.set(LevelFilter.ERRORS.name)
    window.render()
    window.copy_all()
    assert root.clipboard_get() == "\n".join([HEADER, *LINES[2:]]) + "\n"


def test_new_lines_are_followed(root, log):
    window = make_window(root, log)
    with log.open("a", encoding="utf-8") as stream:
        stream.write("2026-10-07 10:00:03,000 - StreamDock - INFO - willAppear\n")
    window._tick()
    assert window.listbox.get(tk.END).endswith("willAppear")


def test_console_without_display_exits_cleanly(log, monkeypatch):
    def no_display() -> tk.Tk:
        raise console_window.NoDisplay("no display name")

    monkeypatch.setattr(console_window, "create_root", no_display)
    assert run_console([str(log), "--smoke"]) == EXIT_NO_DISPLAY


def test_console_smoke_mode_builds_and_closes_window(root, log):
    assert run_console([str(log), "--smoke"]) == EXIT_OK
