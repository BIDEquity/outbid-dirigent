"""
Pytest configuration for outbid-dirigent tests.

This file sets up the Python path so tests can import the source code
without needing to install the package.
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock the version for tests (since package isn't installed)
import outbid_dirigent
outbid_dirigent.__version__ = "test"

import os
import subprocess
import pytest
import outbid_dirigent.logger as logger_mod
from outbid_dirigent.logger import DirigentLogger, init_logger


@pytest.fixture(autouse=True)
def _init_logger(tmp_path):
    """Initialize the global logger singleton for every test, using tmp_path."""
    logger_mod._logger_instance = None
    init_logger(repo_path=str(tmp_path), verbose=False, output_json=False)
    yield
    logger_mod._logger_instance = None


@pytest.fixture
def dirigent_dir(tmp_path):
    """Create and return a .dirigent directory inside tmp_path."""
    d = tmp_path / ".dirigent"
    d.mkdir(exist_ok=True)
    return d


@pytest.fixture
def git_repo(tmp_path):
    """Create a minimal git repo with one initial commit in tmp_path."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


@pytest.fixture
def fake_claude_env(tmp_path, git_repo, monkeypatch):
    """Git repo with fake claude on PATH for E2E testing.

    Returns the repo path. All subprocess calls to 'claude' will hit
    the deterministic fake instead of the real CLI.
    """
    # Create a bin/ dir with a 'claude' wrapper that runs our fake
    bin_dir = tmp_path / "fake_bin"
    bin_dir.mkdir()
    fake_claude_src = Path(__file__).parent / "fake_claude.py"
    claude_wrapper = bin_dir / "claude"
    claude_wrapper.write_text(
        f"#!/usr/bin/env python3\n"
        f"import runpy, sys\n"
        f"sys.argv[0] = {str(fake_claude_src)!r}\n"
        f"runpy.run_path({str(fake_claude_src)!r}, run_name='__main__')\n"
    )
    claude_wrapper.chmod(0o755)

    # Prepend to PATH
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")

    # Create .dirigent dir and a spec
    dirigent_dir = git_repo / ".dirigent"
    dirigent_dir.mkdir(exist_ok=True)
    spec = git_repo / "SPEC.md"
    spec.write_text("# Test Feature\n\nAdd a hello world function.\n")
    (dirigent_dir / "SPEC.md").write_text(spec.read_text())

    return git_repo
