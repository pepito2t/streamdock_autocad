import logging
import os
import subprocess
import sys
import tkinter as tk
from collections import deque
from pathlib import Path
from tkinter import ttk
from typing import Callable

from src.console.instance import SingleInstance
from src.console.journal import (
    LEVEL_FILTER_LABELS,
    LevelFilter,
    LogFollower,
    LogLine,
    copy_text,
    current_header,
    matches,
    parse_lines,
)

WINDOW_TITLE = "Journal du plugin AutoCAD"
WINDOW_SIZE = "1100x600"
POLL_INTERVAL_MS = 500
FRONT_RESTORE_MS = 300
MAX_KEPT_LINES = 5000
SCROLLED_TO_END = 0.999
PADDING = 6
ERROR_COLOR = "#c0392b"
WARNING_COLOR = "#b9770e"
NO_SELECTION = "Sélectionnez d'abord des lignes (clic, Maj+clic ou Ctrl+clic)."
NOTHING_TO_COPY = "Aucune ligne à copier."
COPIED = "{count} ligne(s) copiée(s) : collez-les dans votre courriel avec Ctrl+V."
MISSING_LOG = "Journal introuvable ({path}) : il s'affichera dès que le plugin écrira."
READ_FAILED = "Lecture du journal impossible : {error}"
OPEN_FAILED = "Impossible d'ouvrir le dossier des journaux : {error}"


class NoDisplay(Exception):
    pass


def open_folder(folder: Path) -> None:
    if os.name == "nt":
        os.startfile(folder)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def create_root() -> tk.Tk:
    try:
        return tk.Tk()
    except tk.TclError as error:
        raise NoDisplay(str(error)) from error


def line_color(line: LogLine) -> str | None:
    if line.level >= logging.ERROR:
        return ERROR_COLOR
    if line.level >= logging.WARNING:
        return WARNING_COLOR
    return None


class ConsoleWindow:
    def __init__(
        self,
        root: tk.Tk,
        follower: LogFollower,
        instance: SingleInstance | None = None,
        header: Callable[[], str] = current_header,
    ) -> None:
        self.root = root
        self.follower = follower
        self.instance = instance
        self.header = header
        self.lines: deque[LogLine] = deque(maxlen=MAX_KEPT_LINES)
        self.visible: list[LogLine] = []
        self.level_filter = tk.StringVar(root, LevelFilter.ALL.name)
        self.always_on_top = tk.BooleanVar(root, False)
        self.status = tk.StringVar(root, "")
        self._build()

    def start(self) -> None:
        if not self.follower.path.is_file():
            self.status.set(MISSING_LOG.format(path=self.follower.path))
        self._append(self.follower.start())
        self.root.after(POLL_INTERVAL_MS, self._tick)

    def copy_selection(self) -> None:
        selected = [self.visible[index].text for index in self.listbox.curselection()]
        if not selected:
            self.status.set(NO_SELECTION)
            return
        self._copy(selected)

    def copy_all(self) -> None:
        if not self.visible:
            self.status.set(NOTHING_TO_COPY)
            return
        self._copy([line.text for line in self.visible])

    def open_log_folder(self) -> None:
        try:
            open_folder(self.follower.path.parent)
        except OSError as error:
            self.status.set(OPEN_FAILED.format(error=error))

    def bring_to_front(self) -> None:
        self.root.deiconify()
        self.root.lift()
        # Windows refuses focus to a background process; a short topmost pass brings the window up anyway.
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(FRONT_RESTORE_MS, self._apply_topmost)

    def render(self) -> None:
        self.listbox.delete(0, tk.END)
        self.visible = []
        self._insert([line for line in self.lines if matches(line, self._current_filter())])
        self.listbox.see(tk.END)

    def _build(self) -> None:
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self._build_toolbar()
        self._build_actions()
        self._build_list()
        self.root.bind("<Control-c>", lambda event: self.copy_selection())
        self.root.bind("<Control-a>", lambda event: self.listbox.selection_set(0, tk.END))

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=PADDING)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(toolbar, text="Afficher :").pack(side=tk.LEFT)
        for level_filter, label in LEVEL_FILTER_LABELS.items():
            ttk.Radiobutton(
                toolbar, text=label, value=level_filter.name, variable=self.level_filter, command=self.render
            ).pack(side=tk.LEFT, padx=PADDING)
        ttk.Checkbutton(
            toolbar, text="Toujours au premier plan", variable=self.always_on_top, command=self._apply_topmost
        ).pack(side=tk.RIGHT)

    def _build_actions(self) -> None:
        actions = ttk.Frame(self.root, padding=PADDING)
        actions.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(actions, text="Copier la sélection", command=self.copy_selection).pack(side=tk.LEFT)
        ttk.Button(actions, text="Tout copier", command=self.copy_all).pack(side=tk.LEFT, padx=PADDING)
        ttk.Button(actions, text="Ouvrir le dossier des journaux", command=self.open_log_folder).pack(side=tk.LEFT)
        ttk.Label(actions, textvariable=self.status).pack(side=tk.LEFT, padx=PADDING)

    def _build_list(self) -> None:
        body = ttk.Frame(self.root, padding=(PADDING, 0))
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.listbox = tk.Listbox(
            body, selectmode=tk.EXTENDED, font="TkFixedFont", activestyle="none", exportselection=False
        )
        vertical = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.listbox.yview)
        horizontal = ttk.Scrollbar(body, orient=tk.HORIZONTAL, command=self.listbox.xview)
        self.listbox.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side=tk.RIGHT, fill=tk.Y)
        horizontal.pack(side=tk.BOTTOM, fill=tk.X)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _current_filter(self) -> LevelFilter:
        return LevelFilter[self.level_filter.get()]

    def _apply_topmost(self) -> None:
        self.root.attributes("-topmost", self.always_on_top.get())

    def _tick(self) -> None:
        try:
            self._append(self.follower.poll())
        except OSError as error:
            self.status.set(READ_FAILED.format(error=error))
        if self.instance is not None and self.instance.focus_requested():
            self.bring_to_front()
        self.root.after(POLL_INTERVAL_MS, self._tick)

    def _append(self, texts: list[str]) -> None:
        if not texts:
            return
        previous_level = self.lines[-1].level if self.lines else logging.INFO
        parsed = parse_lines(texts, previous_level)
        self.lines.extend(parsed)
        was_at_end = self.listbox.yview()[1] >= SCROLLED_TO_END
        self._insert([line for line in parsed if matches(line, self._current_filter())])
        if was_at_end:
            self.listbox.see(tk.END)

    def _insert(self, lines: list[LogLine]) -> None:
        for line in lines:
            self.listbox.insert(tk.END, line.text)
            color = line_color(line)
            if color:
                self.listbox.itemconfigure(tk.END, foreground=color)
        self.visible.extend(lines)
        excess = len(self.visible) - MAX_KEPT_LINES
        if excess > 0:
            self.listbox.delete(0, excess - 1)
            del self.visible[:excess]

    def _copy(self, lines: list[str]) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(copy_text(self.header(), lines))
        self.status.set(COPIED.format(count=len(lines)))


def run(log_path: Path, instance: SingleInstance | None, smoke: bool = False) -> int:
    root = create_root()
    window = ConsoleWindow(root, LogFollower(log_path), instance)
    window.start()
    if smoke:
        root.update_idletasks()
        root.destroy()
        return len(window.lines)
    root.mainloop()
    return len(window.lines)
