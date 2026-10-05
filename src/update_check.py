import json
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable

from src.core.logger import Logger
from src.paths import plugin_dir

RELEASES_API = "https://api.github.com/repos/pepito2t/streamdock_autocad/releases/latest"
RELEASES_PAGE = "https://github.com/pepito2t/streamdock_autocad/releases/latest"
HTTP_TIMEOUT_S = 5
CHECK_INTERVAL_S = 6 * 3600
VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    url: str


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.match(text.strip())
    if not match:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def is_newer(candidate: str, current: str) -> bool:
    parsed_candidate, parsed_current = parse_version(candidate), parse_version(current)
    if parsed_candidate is None or parsed_current is None:
        return False
    return parsed_candidate > parsed_current


def installed_version() -> str:
    manifest = json.loads((plugin_dir() / "manifest.json").read_text(encoding="utf-8"))
    return str(manifest["Version"])


def fetch_latest_tag() -> str:
    request = urllib.request.Request(RELEASES_API, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
        return str(json.load(response)["tag_name"])


class UpdateChecker:
    def __init__(self, fetch: Callable[[], str] = fetch_latest_tag, current: Callable[[], str] = installed_version) -> None:
        self._fetch = fetch
        self._current = current
        self._lock = threading.Lock()
        self._available: UpdateInfo | None = None
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._loop, name="update-check", daemon=True).start()

    def check_once(self) -> UpdateInfo | None:
        try:
            latest, current = self._fetch(), self._current()
        except (urllib.error.URLError, OSError, ValueError, KeyError) as error:
            Logger.warning(f"[UpdateChecker] check failed: {error}")
            return self.available()
        info = UpdateInfo(latest.removeprefix("v"), RELEASES_PAGE) if is_newer(latest, current) else None
        with self._lock:
            self._available = info
        return info

    def available(self) -> UpdateInfo | None:
        with self._lock:
            return self._available

    def _loop(self) -> None:
        stop = threading.Event()
        while True:
            self.check_once()
            stop.wait(CHECK_INTERVAL_S)


_checker: UpdateChecker | None = None


def get_checker() -> UpdateChecker:
    global _checker
    if _checker is None:
        _checker = UpdateChecker()
    return _checker
