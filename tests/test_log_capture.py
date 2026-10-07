import json
import logging

import pytest

from src.core import logger as logger_module
from src.core.log_capture import MASK, MemoryLogHandler, SecretMaskingFilter

DRAWFLOW_TOKEN = "Zx9-drawflow-secret"
HEX_TOKEN = "0123456789abcdef0123456789abcdef"


def make_logger(handler: logging.Handler, secret_filter: SecretMaskingFilter) -> logging.Logger:
    logger = logging.getLogger(f"test-{id(handler)}")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    handler.addFilter(secret_filter)
    logger.addHandler(handler)
    return logger


@pytest.fixture
def memory() -> MemoryLogHandler:
    return MemoryLogHandler(capacity=3)


def test_memory_keeps_last_lines_only(memory):
    logger = make_logger(memory, SecretMaskingFilter())
    for index in range(5):
        logger.info("line %d", index)
    assert memory.lines() == ["INFO - line 2", "INFO - line 3", "INFO - line 4"]


def test_memory_counts_errors_until_marked_seen(memory):
    logger = make_logger(memory, SecretMaskingFilter())
    logger.warning("w")
    logger.error("e1")
    logger.critical("e2")
    assert memory.unseen_errors() == 2
    memory.mark_errors_seen()
    assert memory.unseen_errors() == 0
    logger.error("e3")
    assert memory.unseen_errors() == 1


@pytest.mark.parametrize(
    "message",
    [
        f"hello {DRAWFLOW_TOKEN} done",
        f"url ws://127.0.0.1:1?token={DRAWFLOW_TOKEN}",
        f"context {HEX_TOKEN.upper()}",
        f"sha {HEX_TOKEN}{HEX_TOKEN}",
        json.dumps({"type": "hello", "token": "short-but-secret"}),
        "Token: abcdefgh",
    ],
)
def test_secrets_are_masked(message):
    masked = SecretMaskingFilter(lambda: [DRAWFLOW_TOKEN]).mask(message)
    for secret in (DRAWFLOW_TOKEN, HEX_TOKEN, HEX_TOKEN.upper(), "short-but-secret", "abcdefgh"):
        assert secret not in masked
    assert MASK in masked


def test_ordinary_text_is_kept():
    text = "Fichier C:\\Plans\\Drawing1.dwg envoyé, context 1234-abcd, port 23519"
    assert SecretMaskingFilter(lambda: ["x"]).mask(text) == text


def test_masking_applies_to_arguments_and_tracebacks(memory):
    logger = make_logger(memory, SecretMaskingFilter(lambda: [DRAWFLOW_TOKEN]))
    try:
        raise ValueError(f"bad {DRAWFLOW_TOKEN}")
    except ValueError:
        logger.exception("failed with %s", DRAWFLOW_TOKEN)
    output = "\n".join(memory.lines())
    assert DRAWFLOW_TOKEN not in output
    assert "ValueError" in output


def test_known_secrets_are_reloaded_after_refresh_delay():
    now = [0.0]
    secrets = ["first-secret"]
    secret_filter = SecretMaskingFilter(lambda: list(secrets), refresh_s=30, clock=lambda: now[0])
    assert secret_filter.mask("first-secret") == MASK
    secrets[:] = ["second-secret"]
    assert secret_filter.mask("second-secret") == "second-secret"
    now[0] = 31
    assert secret_filter.mask("second-secret") == MASK


def test_unreadable_secret_source_keeps_masking_patterns():
    def broken() -> list[str]:
        raise OSError("locked")

    assert SecretMaskingFilter(broken).mask(f"token={DRAWFLOW_TOKEN}") == f"token={MASK}"


def test_drawflow_token_is_read_from_integrations_file(tmp_path, monkeypatch):
    config = tmp_path / "integrations.json"
    config.write_text(json.dumps({"enabled": True, "port": 4000, "token": DRAWFLOW_TOKEN}), encoding="utf-8")
    monkeypatch.setenv("STREAMDOCK_DRAWFLOW_CONFIG", str(config))
    assert logger_module.drawflow_tokens() == [DRAWFLOW_TOKEN]


def test_plugin_logger_masks_every_handler(tmp_path, monkeypatch):
    config = tmp_path / "integrations.json"
    config.write_text(json.dumps({"enabled": True, "port": 4000, "token": DRAWFLOW_TOKEN}), encoding="utf-8")
    monkeypatch.setenv("STREAMDOCK_DRAWFLOW_CONFIG", str(config))
    plugin_logger = logger_module.Logger.get_logger()
    assert plugin_logger.handlers
    for handler in plugin_logger.handlers:
        assert any(isinstance(item, SecretMaskingFilter) for item in handler.filters)
    assert any(isinstance(handler, MemoryLogHandler) for handler in plugin_logger.handlers)
