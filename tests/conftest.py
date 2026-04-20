"""
Pytest configuration and shared fixtures for Dirigent tests.

This file sets up the Python path so tests can import the source code
without needing to install the package.

Contains fixtures for:
- Unit tests with mocks (fake_claude_env)
- Integration tests with mock portal (mock_portal, test_repo)
- E2E tests with real Claude Code (--e2e flag)
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from typing import Generator, List, Tuple, Optional
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Mock the version for tests (since package isn't installed).
# Imports below must follow the sys.path.insert() above, so they're
# legitimately module-level-but-not-at-top.
import outbid_dirigent  # noqa: E402

outbid_dirigent.__version__ = "test"

import outbid_dirigent.logger as logger_mod  # noqa: E402
from outbid_dirigent.logger import init_logger  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# PYTEST CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Run E2E tests with real Claude Code (requires ANTHROPIC_API_KEY)",
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end (requires --e2e flag and ANTHROPIC_API_KEY)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip E2E tests unless --e2e flag is passed."""
    if config.getoption("--e2e"):
        return  # Don't skip E2E tests

    skip_e2e = pytest.mark.skip(reason="E2E tests disabled. Use --e2e to enable.")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


# ══════════════════════════════════════════════════════════════════════════════
# LOGGER FIXTURE (autouse)
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _init_logger(tmp_path):
    """Initialize the global logger singleton for every test, using tmp_path."""
    logger_mod._logger_instance = None
    init_logger(repo_path=str(tmp_path), verbose=False, output_json=False)
    yield
    logger_mod._logger_instance = None


# ══════════════════════════════════════════════════════════════════════════════
# UNIT TEST FIXTURES
# ══════════════════════════════════════════════════════════════════════════════


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
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True
    )
    (tmp_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True
    )
    return tmp_path


@pytest.fixture
def fake_claude_env(tmp_path, git_repo, monkeypatch):
    """Git repo where TaskRunner calls are intercepted by fake_claude.py.

    The SDK uses a bundled claude binary that ignores PATH, so we patch
    TaskRunner._run_claude and ._run_claude_structured directly to call
    fake_claude.py via subprocess instead.
    """
    from outbid_dirigent.task_runner import TaskRunner

    fake_claude_src = Path(__file__).parent / "fake_claude.py"

    def _invoke_fake(repo_path: Path, prompt: str) -> tuple[bool, str, str]:
        """Run fake_claude.py and return (success, stdout, stderr)."""
        import sys

        env = {**os.environ, "PWD": str(repo_path)}
        result = subprocess.run(
            [sys.executable, str(fake_claude_src), "-p", prompt],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            env=env,
        )
        return result.returncode == 0, result.stdout, result.stderr

    def fake_run_claude(
        self, prompt, timeout=0, model="", effort="", system_prompt="", component="", **_kwargs
    ):
        return _invoke_fake(self.repo_path, prompt)

    def fake_run_claude_structured(
        self,
        prompt,
        output_format,
        timeout=0,
        model="",
        effort="",
        system_prompt="",
        agents=None,
        component="",
        **_kwargs,
    ):
        _invoke_fake(self.repo_path, prompt)

        # Detect which file was written and return it as structured dict
        _agent_to_skill = {
            "contract-negotiator": "create-contract",
            "reviewer": "review-phase",
            "implementer": "fix-review",
        }
        skill = next(
            (
                s
                for s in [
                    "create-plan",
                    "implement-task",
                    "create-contract",
                    "review-phase",
                    "fix-review",
                ]
                if f"/dirigent:{s}" in prompt
            ),
            None,
        )
        if skill is None:
            skill = next(
                (s for name, s in _agent_to_skill.items() if f"{name} agent" in prompt), "unknown"
            )
        dd = self.dirigent_dir

        try:
            if skill == "create-plan":
                return True, json.loads((dd / "PLAN.json").read_text())
            elif skill == "create-contract":
                import re

                m = re.search(r"phase[_\-\s]+id[\"'\s:=]+[\"']?(\w+)", prompt, re.IGNORECASE)
                phase_id = m.group(1) if m else "01"
                path = dd / "contracts" / f"phase-{phase_id}.json"
                return True, json.loads(path.read_text())
            elif skill == "review-phase":
                import re

                m = re.search(r"phase[_\-\s]+id[\"'\s:=]+[\"']?(\w+)", prompt, re.IGNORECASE)
                phase_id = m.group(1) if m else "01"
                path = dd / "reviews" / f"phase-{phase_id}.json"
                return True, json.loads(path.read_text())
        except Exception:
            pass

        return False, None

    monkeypatch.setattr(TaskRunner, "_run_claude", fake_run_claude)
    monkeypatch.setattr(TaskRunner, "_run_claude_structured", fake_run_claude_structured)

    # Create .dirigent dir and a spec
    dirigent_dir = git_repo / ".dirigent"
    dirigent_dir.mkdir(exist_ok=True)
    spec = git_repo / "SPEC.md"
    spec.write_text("# Test Feature\n\nAdd a hello world function.\n")
    (dirigent_dir / "SPEC.md").write_text(spec.read_text())

    return git_repo


# ══════════════════════════════════════════════════════════════════════════════
# MOCK PORTAL FIXTURES
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class PortalEvent:
    """Captured event from Dirigent to Portal."""

    event_type: str
    data: dict
    timestamp: str


@dataclass
class MockPortalState:
    """State for the mock portal server."""

    events: List[PortalEvent] = field(default_factory=list)
    pending_execution: Optional[dict] = None
    execution_claimed: bool = False


class MockPortalHandler(BaseHTTPRequestHandler):
    """HTTP handler that simulates Portal API endpoints."""

    state: MockPortalState = None  # Set by fixture

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path.startswith("/api/pending-execution"):
            if self.state.pending_execution and not self.state.execution_claimed:
                self._send_json({"pending": True, **self.state.pending_execution})
            else:
                self._send_json({"pending": False})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if self.path == "/api/pending-execution":
            # Claim execution
            self.state.execution_claimed = True
            self._send_json({"success": True})

        elif self.path == "/api/execution-event":
            # Capture event
            event_data = data.get("event", {})
            event = PortalEvent(
                event_type=event_data.get("type", "unknown"),
                data=event_data.get("data", {}),
                timestamp=event_data.get("ts", ""),
            )
            self.state.events.append(event)
            self._send_json({"success": True})

        else:
            self._send_json({"error": "Not found"}, 404)


@pytest.fixture
def mock_portal() -> Generator[Tuple[str, MockPortalState], None, None]:
    """
    Start a mock portal server and return its URL and state.

    Usage:
        def test_something(mock_portal):
            url, state = mock_portal
            state.pending_execution = {"execution_id": "test-123", ...}
            # Run dirigent with portal_url=url
            assert len(state.events) > 0
    """
    state = MockPortalState()
    MockPortalHandler.state = state

    server = HTTPServer(("127.0.0.1", 0), MockPortalHandler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}"

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    yield url, state

    server.shutdown()


# ══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TEST FIXTURES
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_repo() -> Generator[Path, None, None]:
    """
    Create a temporary git repository for testing.

    Initializes a basic Node.js project structure.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Create package.json
        package_json = {
            "name": "test-repo",
            "version": "1.0.0",
            "scripts": {"test": "echo 'no tests'"},
        }
        (repo_path / "package.json").write_text(json.dumps(package_json, indent=2))

        # Create README
        (repo_path / "README.md").write_text("# Test Repository\n\nFor integration testing.\n")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        yield repo_path


@pytest.fixture
def spec_file(test_repo: Path) -> Path:
    """
    Create a SPEC.md file in the test repo's .planning directory.

    Returns the path to the spec file.
    """
    planning_dir = test_repo / ".planning"
    planning_dir.mkdir(exist_ok=True)

    spec_path = planning_dir / "SPEC.md"
    spec_path.write_text("""# Test Feature

## Beschreibung
Erstelle eine einfache hello.txt Datei im Root-Verzeichnis.

## Akzeptanzkriterien
- [ ] hello.txt existiert im Root
- [ ] Inhalt ist "Hello, World!"

## Technische Details
- Einfache Textdatei
- UTF-8 Encoding
""")

    # Commit the spec
    subprocess.run(["git", "add", "."], cwd=test_repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add spec"], cwd=test_repo, check=True, capture_output=True
    )

    return spec_path


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════


def count_commits(repo_path: Path) -> int:
    """Count the number of commits in the repo."""
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], cwd=repo_path, capture_output=True, text=True
    )
    return int(result.stdout.strip())


def get_commit_messages(repo_path: Path, count: int = 10) -> List[str]:
    """Get recent commit messages."""
    result = subprocess.run(
        ["git", "log", f"-{count}", "--format=%s"], cwd=repo_path, capture_output=True, text=True
    )
    return result.stdout.strip().split("\n")


def file_exists(repo_path: Path, filename: str) -> bool:
    """Check if a file exists in the repo."""
    return (repo_path / filename).exists()


def get_file_content(repo_path: Path, filename: str) -> str:
    """Get content of a file in the repo."""
    return (repo_path / filename).read_text()
