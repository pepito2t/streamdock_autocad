from pathlib import Path

import pytest

from src.actions.console import ConsoleAction, console_title, write_memory_snapshot
from src.console.launcher import ConsoleLaunchError
from src.core.logger import Logger


@pytest.fixture(autouse=True)
def no_unseen_errors():
    Logger.memory().mark_errors_seen()
    yield
    Logger.memory().mark_errors_seen()


def make_console(plugin, launched: list[Path]) -> ConsoleAction:
    action = ConsoleAction("com.tmbk.streamdock.autocad.console", "ctx-console", {}, plugin)
    action.launch = launched.append
    return action


def titles(plugin) -> list[str]:
    return [event["payload"]["title"] for event in plugin.ws.events("setTitle")]


def test_console_title_counts_unseen_errors():
    assert console_title(0) == "Console"
    assert console_title(1) == "Console\n1 erreur"
    assert console_title(3) == "Console\n3 erreurs"
    assert console_title(250) == "Console\n99+ erreurs"


def test_key_shows_unseen_errors(bridge, plugin):
    make_console(plugin, [])
    Logger.error("boom")
    Logger.error("boom again")
    plugin.timer.fire_all()
    assert titles(plugin) == ["Console", "Console\n2 erreurs"]


def test_press_opens_console_on_plugin_log_and_resets_count(bridge, plugin):
    launched: list[Path] = []
    action = make_console(plugin, launched)
    Logger.error("boom")
    action.on_key_up({})
    assert launched == [Logger.log_file()]
    assert Logger.memory().unseen_errors() == 0
    assert titles(plugin)[-1] == "Console"
    assert plugin.ws.events("showOk")


def test_launch_failure_is_reported(bridge, plugin):
    action = make_console(plugin, [])

    def failing(path: Path) -> None:
        raise ConsoleLaunchError("Impossible d'ouvrir la console du plugin : accès refusé")

    action.launch = failing
    action.on_key_up({})
    assert plugin.ws.events("showAlert")
    assert "console" in plugin.ws.events("sendToPropertyInspector")[-1]["payload"]["message"]


def test_memory_snapshot_is_used_without_log_file(bridge, plugin, monkeypatch, tmp_path):
    monkeypatch.setattr(Logger, "log_file", classmethod(lambda cls: None))
    monkeypatch.setattr("src.console.instance.instance_dir", lambda: tmp_path)
    launched: list[Path] = []
    Logger.info("kept in memory")
    make_console(plugin, launched).on_key_up({})
    assert launched == [tmp_path / "plugin-snapshot.log"]
    assert "kept in memory" in launched[0].read_text(encoding="utf-8")


def test_snapshot_writes_memory_lines(tmp_path):
    Logger.info("snapshot line")
    target = write_memory_snapshot(tmp_path / "sub" / "snap.log")
    assert target.read_text(encoding="utf-8").splitlines()[-1].endswith("snapshot line")
