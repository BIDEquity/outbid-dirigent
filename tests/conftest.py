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
