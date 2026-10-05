import json
from pathlib import Path

import pytest

from src.bridge import set_bridge
from src.bridge.autocad_fake import FakeAutocadBridge
from src.core.timer import Timer


class FakeSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def send(self, raw: str) -> None:
        self.messages.append(json.loads(raw))

    def events(self, name: str) -> list[dict]:
        return [message for message in self.messages if message["event"] == name]


class FakeTimer(Timer):
    def __init__(self) -> None:
        self._intervals = {}

    def fire_all(self) -> None:
        for data in list(self._intervals.values()):
            data["callback"]()


class FakePlugin:
    def __init__(self) -> None:
        self.ws = FakeSocket()
        self.timer = FakeTimer()


@pytest.fixture
def bridge() -> FakeAutocadBridge:
    fake = FakeAutocadBridge()
    set_bridge(fake)
    return fake


@pytest.fixture
def plugin() -> FakePlugin:
    return FakePlugin()


@pytest.fixture
def preset_dirs(tmp_path: Path) -> tuple[Path, Path]:
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    (bundled / "zoom.json").write_text(json.dumps({"name": "Zoom", "steps": ["_.ZOOM _E"]}), encoding="utf-8")
    return bundled, tmp_path / "user"


@pytest.fixture(autouse=True)
def fresh_state():
    from src.autocad_state import get_state

    get_state().invalidate()
