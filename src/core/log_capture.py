import logging
import re
import threading
import time
from collections import deque
from typing import Callable, Iterable

MEMORY_CAPACITY = 2000
MASK = "***"
MIN_SECRET_LENGTH = 8
SECRET_REFRESH_S = 30.0
HEX_SECRET = re.compile(r"\b[0-9a-fA-F]{32,}\b")
TOKEN_ASSIGNMENT = re.compile(r"""(["']?token["']?\s*[=:]\s*["']?)[^\s"',;&}]+""", re.IGNORECASE)

SecretSource = Callable[[], Iterable[str]]


class SecretMaskingFilter(logging.Filter):
    """Masks secrets in every record so neither the log file nor the console ever shows them."""

    def __init__(
        self,
        known_secrets: SecretSource = lambda: (),
        refresh_s: float = SECRET_REFRESH_S,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        super().__init__()
        self._known_secrets = known_secrets
        self._refresh_s = refresh_s
        self._clock = clock
        self._lock = threading.Lock()
        self._secrets: tuple[str, ...] = ()
        self._loaded_at: float | None = None

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self.mask(record.getMessage())
        record.args = None
        if record.exc_info and not record.exc_text:
            record.exc_text = logging.Formatter().formatException(record.exc_info)
        if record.exc_text:
            record.exc_text = self.mask(record.exc_text)
        if record.stack_info:
            record.stack_info = self.mask(record.stack_info)
        return True

    def mask(self, text: str) -> str:
        for secret in self._current_secrets():
            text = text.replace(secret, MASK)
        text = TOKEN_ASSIGNMENT.sub(lambda match: match.group(1) + MASK, text)
        return HEX_SECRET.sub(MASK, text)

    def _current_secrets(self) -> tuple[str, ...]:
        with self._lock:
            now = self._clock()
            if self._loaded_at is None or now - self._loaded_at >= self._refresh_s:
                self._loaded_at = now
                self._secrets = self._load_secrets()
            return self._secrets

    def _load_secrets(self) -> tuple[str, ...]:
        try:
            secrets = self._known_secrets()
        except (OSError, ValueError):
            return self._secrets
        return tuple(sorted({secret for secret in secrets if len(secret) >= MIN_SECRET_LENGTH}, key=len, reverse=True))


class MemoryLogHandler(logging.Handler):
    """Keeps the last formatted lines and counts errors not yet seen in the console."""

    def __init__(self, capacity: int = MEMORY_CAPACITY) -> None:
        super().__init__()
        self._lines: deque[str] = deque(maxlen=capacity)
        self._unseen_errors = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
        except (TypeError, ValueError, KeyError):
            self.handleError(record)
            return
        self._lines.append(line)
        if record.levelno >= logging.ERROR:
            self._unseen_errors += 1

    def lines(self) -> list[str]:
        with self.lock:
            return list(self._lines)

    def unseen_errors(self) -> int:
        with self.lock:
            return self._unseen_errors

    def mark_errors_seen(self) -> None:
        with self.lock:
            self._unseen_errors = 0
