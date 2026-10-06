import threading
import time
from typing import Any

from src.bridge import get_bridge
from src.bridge.autocad_bridge import AutocadError
from src.core.logger import Logger

WATCHED_VARS = ["CLAYER", "ORTHOMODE", "SNAPMODE", "GRIDMODE", "OSMODE", "LWDISPLAY", "DWGNAME", "DWGPREFIX", "DWGTITLED"]
CACHE_TTL_S = 0.8


class AutocadState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, Any] = {}
        self._connected = False
        self._fetched_at = 0.0

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            if time.monotonic() - self._fetched_at >= CACHE_TTL_S:
                self._refresh()
            return dict(self._values) if self._connected else None

    def _refresh(self) -> None:
        self._fetched_at = time.monotonic()
        try:
            self._values = get_bridge().get_vars(WATCHED_VARS)
            self._connected = True
        except AutocadError as error:
            if self._connected:
                Logger.warning(f"[AutocadState] lost AutoCAD: {error}")
            self._values = {}
            self._connected = False

    def invalidate(self) -> None:
        with self._lock:
            self._fetched_at = 0.0


_state: AutocadState | None = None


def get_state() -> AutocadState:
    global _state
    if _state is None:
        _state = AutocadState()
    return _state
