"""Smoke tests for Executor.harness_install.

Covers:
- Idempotency: harness-docs/ already present → skip, no subprocess.
- Happy path via OUTBID_HARNESS_PATH: runs local install.sh, harness-docs/ appears.
- Failure modes: missing install.sh, installer exits non-zero, installer leaves
  harness-docs/ absent.

Uses a stub object bound to Executor.harness_install so we avoid the full
Executor dependency graph (RunDir, TaskRunner, Shipper, etc.).
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import MethodType, SimpleNamespace
from typing import cast

from outbid_dirigent.executor import Executor


def _make_stub(repo: Path) -> Executor:
    """Minimal object with only what harness_install needs.

    Uses SimpleNamespace + MethodType so the method can be invoked as a
    bound call while avoiding the full Executor dependency graph. Cast to
    Executor so callers are typed cleanly.
    """
    stub = SimpleNamespace(repo_path=repo)
    stub.harness_install = MethodType(Executor.harness_install, stub)
    return cast(Executor, stub)


def _write_installer(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


FAKE_INSTALLER_CREATES_DOCS = """#!/usr/bin/env bash
set -e
target=""
while [ $# -gt 0 ]; do
    case "$1" in
        --target) target="$2"; shift 2 ;;
        --yes) shift ;;
        *) shift ;;
    esac
done
mkdir -p "$target/harness-docs"
"""


class TestHarnessInstallIdempotency:
    def test_skips_when_harness_docs_present(self, tmp_path, monkeypatch):
        """harness-docs/ already exists → returns True without touching env / subprocess."""
        (tmp_path / "harness-docs").mkdir()
        # Point env var at a bogus path — if we shell out, the installer would fail
        # and we'd see False. Idempotency must short-circuit before that.
        monkeypatch.setenv("OUTBID_HARNESS_PATH", "/definitely/not/a/real/path")

        assert _make_stub(tmp_path).harness_install() is True


class TestHarnessInstallViaLocalPath:
    def test_runs_local_install_sh(self, tmp_path, monkeypatch):
        """OUTBID_HARNESS_PATH → install.sh runs with --target <repo> --yes."""
        harness_dir = tmp_path / "harness"
        harness_dir.mkdir()
        _write_installer(harness_dir / "install.sh", FAKE_INSTALLER_CREATES_DOCS)

        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setenv("OUTBID_HARNESS_PATH", str(harness_dir))

        assert _make_stub(repo).harness_install() is True
        assert (repo / "harness-docs").is_dir()


class TestHarnessInstallFailureModes:
    def test_returns_false_when_install_sh_missing(self, tmp_path, monkeypatch):
        """OUTBID_HARNESS_PATH points at a dir without install.sh."""
        harness_dir = tmp_path / "harness"
        harness_dir.mkdir()  # no install.sh inside
        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setenv("OUTBID_HARNESS_PATH", str(harness_dir))

        assert _make_stub(repo).harness_install() is False

    def test_returns_false_when_installer_exits_nonzero(self, tmp_path, monkeypatch):
        harness_dir = tmp_path / "harness"
        harness_dir.mkdir()
        _write_installer(harness_dir / "install.sh", "#!/usr/bin/env bash\nexit 2\n")
        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setenv("OUTBID_HARNESS_PATH", str(harness_dir))

        assert _make_stub(repo).harness_install() is False

    def test_returns_false_when_installer_succeeds_but_docs_not_created(
        self, tmp_path, monkeypatch
    ):
        """Post-condition check: installer exits 0, but harness-docs/ still absent."""
        harness_dir = tmp_path / "harness"
        harness_dir.mkdir()
        _write_installer(harness_dir / "install.sh", "#!/usr/bin/env bash\nexit 0\n")
        repo = tmp_path / "repo"
        repo.mkdir()
        monkeypatch.setenv("OUTBID_HARNESS_PATH", str(harness_dir))

        assert _make_stub(repo).harness_install() is False
