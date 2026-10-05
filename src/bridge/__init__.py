import sys

from src.bridge.autocad_bridge import AutocadBridge

_bridge: AutocadBridge | None = None


def get_bridge() -> AutocadBridge:
    global _bridge
    if _bridge is None:
        _bridge = _create_bridge()
    return _bridge


def set_bridge(bridge: AutocadBridge) -> None:
    global _bridge
    _bridge = bridge


def _create_bridge() -> AutocadBridge:
    if sys.platform == "win32":
        from src.bridge.autocad_com import ComAutocadBridge

        return ComAutocadBridge()
    from src.bridge.autocad_fake import FakeAutocadBridge

    return FakeAutocadBridge()
