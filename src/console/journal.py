import logging
import platform
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable

INITIAL_LINES = 1000
TAIL_CHUNK_BYTES = 64 * 1024
ENCODING = "utf-8"
UNKNOWN_VERSION = "?"
LINE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - \S+ - (?P<level>[A-Z]+) - ")


class LevelFilter(Enum):
    ALL = logging.NOTSET
    WARNINGS = logging.WARNING
    ERRORS = logging.ERROR


LEVEL_FILTER_LABELS = {
    LevelFilter.ALL: "Tout",
    LevelFilter.WARNINGS: "Avertissements et erreurs",
    LevelFilter.ERRORS: "Erreurs",
}


@dataclass(frozen=True)
class LogLine:
    text: str
    level: int


def parse_lines(texts: Iterable[str], previous_level: int = logging.INFO) -> list[LogLine]:
    """Continuation lines (tracebacks, multi-line messages) take the level of the record they belong to."""
    parsed: list[LogLine] = []
    level = previous_level
    for text in texts:
        match = LINE_PATTERN.match(text)
        if match:
            level = logging.getLevelName(match.group("level"))
            level = level if isinstance(level, int) else logging.INFO
        parsed.append(LogLine(text, level))
    return parsed


def matches(line: LogLine, level_filter: LevelFilter) -> bool:
    return line.level >= level_filter.value


def copy_header(version: str, system: str, now: datetime) -> str:
    return f"AutoCAD plugin v{version} · {system} · {now.isoformat(timespec='seconds')}"


def copy_text(header: str, lines: Iterable[str]) -> str:
    return "\n".join([header, *lines]) + "\n"


def system_description() -> str:
    return f"{platform.system()} {platform.release()} ({platform.version()})"


def plugin_version() -> str:
    from src.update_check import installed_version

    try:
        return installed_version()
    except (OSError, ValueError, KeyError):
        return UNKNOWN_VERSION


def current_header() -> str:
    return copy_header(plugin_version(), system_description(), datetime.now().astimezone())


def _decode(raw: bytes) -> str:
    return raw.decode(ENCODING, errors="replace").rstrip("\r")


def read_tail(path: Path, max_lines: int) -> tuple[list[str], int, bytes]:
    """Last complete lines, the byte offset reached and the unterminated last line."""
    try:
        with path.open("rb") as stream:
            end = stream.seek(0, 2)
            start = end
            data = b""
            while start > 0 and data.count(b"\n") <= max_lines:
                start = max(0, start - TAIL_CHUNK_BYTES)
                stream.seek(start)
                data = stream.read(end - start)
    except FileNotFoundError:
        return [], 0, b""
    *complete, pending = data.split(b"\n")
    if start > 0 and complete:
        complete = complete[1:]
    return [_decode(raw) for raw in complete[-max_lines:]], end, pending


class LogFollower:
    """Follows a log file like `tail -f`, restarting from the top when the file is truncated or replaced."""

    def __init__(self, path: Path, initial_lines: int = INITIAL_LINES) -> None:
        self.path = path
        self._initial_lines = initial_lines
        self._offset = 0
        self._pending = b""

    def start(self) -> list[str]:
        lines, self._offset, self._pending = read_tail(self.path, self._initial_lines)
        return lines

    def poll(self) -> list[str]:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return []
        if size < self._offset:
            self._offset, self._pending = 0, b""
        if size == self._offset:
            return []
        with self.path.open("rb") as stream:
            stream.seek(self._offset)
            data = stream.read(size - self._offset)
        self._offset += len(data)
        *complete, self._pending = (self._pending + data).split(b"\n")
        return [_decode(raw) for raw in complete]
