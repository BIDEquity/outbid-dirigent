"""Smoke tests for DirigentLogger's structured-logging guarantees.

The logger must always emit `service`, `trace_id`, `timestamp`, `level`, and
`message` on every JSONL record, per harness-docs/engineering-standards.md §07.
"""

from __future__ import annotations

import json

import pytest

from outbid_dirigent.logger import DirigentLogger


REQUIRED_FIELDS = {"timestamp", "service", "trace_id", "level", "message"}


@pytest.fixture
def logger(tmp_path, monkeypatch):
    monkeypatch.setenv("EXECUTION_ID", "test-exec-42")
    return DirigentLogger(repo_path=str(tmp_path), verbose=False, output_json=False)


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_jsonl_record_has_required_fields(logger):
    logger.info("hello")
    entries = _read_jsonl(logger.json_log_file)

    assert entries, "expected at least one JSONL entry"
    for entry in entries:
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"missing required fields {missing} in {entry!r}"


def test_trace_id_honors_execution_id(logger):
    logger.info("hello")
    entries = _read_jsonl(logger.json_log_file)

    assert entries[-1]["trace_id"] == "test-exec-42"


def test_service_name_is_constant(logger):
    logger.info("hello")
    entries = _read_jsonl(logger.json_log_file)

    assert entries[-1]["service"] == "outbid-dirigent"


def test_trace_id_falls_back_to_uuid_without_execution_id(tmp_path, monkeypatch):
    monkeypatch.delenv("EXECUTION_ID", raising=False)
    logger = DirigentLogger(repo_path=str(tmp_path), verbose=False, output_json=False)
    logger.info("hello")
    entries = _read_jsonl(logger.json_log_file)

    trace_id = entries[-1]["trace_id"]
    assert trace_id, "trace_id must not be empty when EXECUTION_ID is unset"
    assert len(trace_id) == 32, "uuid4().hex fallback should produce a 32-char id"


def test_trace_id_stable_across_entries(logger):
    logger.info("first")
    logger.info("second")
    logger.info("third")
    entries = _read_jsonl(logger.json_log_file)

    trace_ids = {e["trace_id"] for e in entries}
    assert len(trace_ids) == 1, f"trace_id must be stable across a run, got {trace_ids}"


def test_timestamp_is_iso_8601_with_z_suffix(logger):
    logger.info("hello")
    entries = _read_jsonl(logger.json_log_file)

    ts = entries[-1]["timestamp"]
    assert ts.endswith("Z"), f"expected UTC Z-suffixed timestamp, got {ts}"
    assert "T" in ts, f"expected ISO 8601 T separator, got {ts}"
