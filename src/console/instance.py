import os
import tempfile
import time
from pathlib import Path
from typing import IO

INSTANCE_DIR_NAME = "streamdock-autocad-console"
LOCK_FILE = "console.lock"
FOCUS_FILE = "console.focus"
LOCKED_BYTES = 1


def instance_dir() -> Path:
    return Path(tempfile.gettempdir()) / INSTANCE_DIR_NAME


def _try_lock(stream: IO[str]) -> bool:
    try:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, LOCKED_BYTES)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


class SingleInstance:
    """One console window at a time: the OS releases the file lock when the window process exits, even on a crash."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or instance_dir()
        self._lock_stream: IO[str] | None = None
        self._last_focus_request = ""

    @property
    def snapshot_path(self) -> Path:
        return self.directory / "plugin-snapshot.log"

    def acquire(self) -> bool:
        self.directory.mkdir(parents=True, exist_ok=True)
        stream = (self.directory / LOCK_FILE).open("a", encoding="utf-8")
        if not _try_lock(stream):
            stream.close()
            return False
        self._lock_stream = stream
        self._last_focus_request = self._read_focus_request()
        return True

    def release(self) -> None:
        if self._lock_stream is not None:
            self._lock_stream.close()
            self._lock_stream = None

    def is_running(self) -> bool:
        if self._lock_stream is not None:
            return True
        if not self.acquire():
            return True
        self.release()
        return False

    def request_focus(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / FOCUS_FILE).write_text(str(time.time_ns()), encoding="utf-8")

    def focus_requested(self) -> bool:
        current = self._read_focus_request()
        if current == self._last_focus_request:
            return False
        self._last_focus_request = current
        return True

    def _read_focus_request(self) -> str:
        try:
            return (self.directory / FOCUS_FILE).read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""
