"""Tests for the startup toolbox snapshot probe."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from outbid_dirigent.dirigent import _log_toolbox_snapshot
from outbid_dirigent.logger import init_logger


@pytest.fixture(autouse=True)
def logger_fixture(tmp_path):
    init_logger(str(tmp_path), verbose=False, output_json=False, dirigent_dir=tmp_path)


def _ok(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_writes_snapshot_when_cli_present(tmp_path):
    run_dir = tmp_path / "run"
    fake = [
        _ok("Installed plugins:\n  ❯ bid-harness\n  ❯ dirigent\n"),
        _ok("context7: npx -y context7-mcp - ✓ Connected\nplaywright: npx mcp - ✓ Connected\n"),
    ]
    with patch("subprocess.run", side_effect=fake):
        _log_toolbox_snapshot(run_dir)

    snapshot = (run_dir / "toolbox-snapshot.txt").read_text(encoding="utf-8")
    assert "# plugins (exit=0)" in snapshot
    assert "bid-harness" in snapshot
    assert "# mcp (exit=0)" in snapshot
    assert "context7" in snapshot


def test_handles_missing_claude_cli(tmp_path):
    run_dir = tmp_path / "run"
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        _log_toolbox_snapshot(run_dir)

    snapshot = (run_dir / "toolbox-snapshot.txt").read_text(encoding="utf-8")
    assert "claude CLI not on PATH" in snapshot
    assert "# plugins" in snapshot
    assert "# mcp" in snapshot


def test_handles_nonzero_exit(tmp_path):
    run_dir = tmp_path / "run"
    fake = [
        subprocess.CompletedProcess(args=[], returncode=2, stdout="", stderr="oops"),
        _ok("context7: ✓ Connected\n"),
    ]
    with patch("subprocess.run", side_effect=fake):
        _log_toolbox_snapshot(run_dir)

    snapshot = (run_dir / "toolbox-snapshot.txt").read_text(encoding="utf-8")
    assert "# plugins (exit=2)" in snapshot
    assert "oops" in snapshot
    assert "# mcp (exit=0)" in snapshot


def test_handles_timeout(tmp_path):
    run_dir = tmp_path / "run"
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["claude"], timeout=15)):
        _log_toolbox_snapshot(run_dir)

    snapshot = (run_dir / "toolbox-snapshot.txt").read_text(encoding="utf-8")
    assert "timed out after 15s" in snapshot


def test_never_raises_when_run_dir_is_none():
    # Must not raise even if run dir is None (write step is skipped silently).
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        _log_toolbox_snapshot(None)
