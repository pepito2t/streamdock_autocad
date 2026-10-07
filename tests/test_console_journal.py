import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.console.journal import (
    LevelFilter,
    LogFollower,
    LogLine,
    copy_header,
    copy_text,
    matches,
    parse_lines,
    read_tail,
)

INFO_LINE = "2026-10-07 10:00:00,001 - StreamDock - INFO - keyDown"
WARNING_LINE = "2026-10-07 10:00:01,002 - StreamDock - WARNING - [UpdateChecker] check failed"
ERROR_LINE = "2026-10-07 10:00:02,003 - StreamDock - ERROR - [MacroAction] AutoCAD n'est pas ouvert"


def write_log(path: Path, lines: list[str], mode: str = "w") -> None:
    with path.open(mode, encoding="utf-8", newline="") as stream:
        stream.write("".join(line + "\r\n" for line in lines))


def test_levels_are_parsed_and_continuations_inherit():
    lines = parse_lines([INFO_LINE, ERROR_LINE, "Traceback (most recent call last):", "  File x", WARNING_LINE])
    assert [line.level for line in lines] == [
        logging.INFO,
        logging.ERROR,
        logging.ERROR,
        logging.ERROR,
        logging.WARNING,
    ]


def test_leading_continuation_uses_previous_level():
    assert parse_lines(["  File x"], logging.ERROR)[0].level == logging.ERROR


def test_level_filters():
    info, warning, error = parse_lines([INFO_LINE, WARNING_LINE, ERROR_LINE])
    assert all(matches(line, LevelFilter.ALL) for line in (info, warning, error))
    assert [matches(line, LevelFilter.WARNINGS) for line in (info, warning, error)] == [False, True, True]
    assert [matches(line, LevelFilter.ERRORS) for line in (info, warning, error)] == [False, False, True]
    assert matches(LogLine("x", logging.CRITICAL), LevelFilter.ERRORS)


def test_copy_starts_with_support_header():
    now = datetime(2026, 10, 7, 14, 3, 12, tzinfo=timezone(timedelta(hours=2)))
    header = copy_header("0.3.0", "Windows 11 (10.0.22631)", now)
    assert header == "AutoCAD plugin v0.3.0 · Windows 11 (10.0.22631) · 2026-10-07T14:03:12+02:00"
    assert copy_text(header, [INFO_LINE, ERROR_LINE]) == f"{header}\n{INFO_LINE}\n{ERROR_LINE}\n"


def test_tail_returns_last_lines_without_partial_first_line(tmp_path, monkeypatch):
    monkeypatch.setattr("src.console.journal.TAIL_CHUNK_BYTES", 16)
    log = tmp_path / "plugin.log"
    write_log(log, [f"line {index} é" for index in range(50)])
    lines, offset, pending = read_tail(log, 3)
    assert lines == ["line 47 é", "line 48 é", "line 49 é"]
    assert offset == log.stat().st_size
    assert pending == b""


def test_tail_of_short_or_missing_file(tmp_path):
    log = tmp_path / "plugin.log"
    assert read_tail(log, 10) == ([], 0, b"")
    write_log(log, ["a", "b"])
    assert read_tail(log, 10)[0] == ["a", "b"]


def test_follower_reads_new_lines_and_waits_for_line_end(tmp_path):
    log = tmp_path / "plugin.log"
    write_log(log, [INFO_LINE])
    follower = LogFollower(log)
    assert follower.start() == [INFO_LINE]
    assert follower.poll() == []
    with log.open("a", encoding="utf-8", newline="") as stream:
        stream.write("2026-10-07 10:00:03,000 - StreamDock - INFO - par")
    assert follower.poll() == []
    with log.open("a", encoding="utf-8", newline="") as stream:
        stream.write("tiel\r\n")
    assert follower.poll() == ["2026-10-07 10:00:03,000 - StreamDock - INFO - partiel"]


def test_follower_restarts_when_file_is_truncated(tmp_path):
    log = tmp_path / "plugin.log"
    write_log(log, [INFO_LINE, WARNING_LINE])
    follower = LogFollower(log)
    follower.start()
    write_log(log, [ERROR_LINE])
    assert follower.poll() == [ERROR_LINE]


def test_follower_waits_for_missing_file(tmp_path):
    log = tmp_path / "plugin.log"
    follower = LogFollower(log)
    assert follower.start() == []
    assert follower.poll() == []
    write_log(log, [INFO_LINE])
    assert follower.poll() == [INFO_LINE]
