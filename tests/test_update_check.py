from src.update_check import UpdateChecker, is_newer, parse_version


def test_parse_version_accepts_tag_prefix():
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.2.3-rc1") == (1, 2, 3)
    assert parse_version("latest") is None


def test_is_newer_compares_numerically():
    assert is_newer("v0.10.0", "0.9.9")
    assert not is_newer("v0.1.0", "0.1.0")
    assert not is_newer("garbage", "0.1.0")


def test_checker_reports_newer_release():
    checker = UpdateChecker(fetch=lambda: "v0.2.0", current=lambda: "0.1.0")
    info = checker.check_once()
    assert info is not None and info.version == "0.2.0"
    assert checker.available() == info


def test_checker_keeps_quiet_on_network_error():
    def failing() -> str:
        raise OSError("offline")

    checker = UpdateChecker(fetch=failing, current=lambda: "0.1.0")
    assert checker.check_once() is None
