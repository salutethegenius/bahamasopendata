"""Tests for ingestion.intelligence.logging_config."""
from __future__ import annotations

from ingestion.intelligence import logging_config


def test_get_logger_writes_to_file(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "intelligence"
    monkeypatch.setattr(logging_config, "INTELLIGENCE_DATA_DIR", data_dir)

    logger = logging_config.get_logger("test_logging_writes")
    logger.info("capture log test message")

    log_file = data_dir / "logs" / "capture.log"
    assert log_file.exists()
    assert "capture log test message" in log_file.read_text()


def test_get_logger_is_idempotent(tmp_path, monkeypatch):
    data_dir = tmp_path / "data" / "intelligence"
    monkeypatch.setattr(logging_config, "INTELLIGENCE_DATA_DIR", data_dir)

    first = logging_config.get_logger("test_logging_idempotent")
    handler_count = len(first.handlers)
    second = logging_config.get_logger("test_logging_idempotent")

    assert first is second
    assert len(second.handlers) == handler_count
