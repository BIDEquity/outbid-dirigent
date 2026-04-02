"""
Pytest configuration and shared fixtures for Dirigent integration tests.
"""
import os
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Generator, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

import pytest


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Run E2E tests with real Claude Code (requires ANTHROPIC_API_KEY)"
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
                self._send_json({
                    "pending": True,
                    **self.state.pending_execution
                })
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
                timestamp=event_data.get("ts", "")
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
            cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_path, check=True, capture_output=True
        )

        # Create package.json
        package_json = {
            "name": "test-repo",
            "version": "1.0.0",
            "scripts": {
                "test": "echo 'no tests'"
            }
        }
        (repo_path / "package.json").write_text(json.dumps(package_json, indent=2))

        # Create README
        (repo_path / "README.md").write_text("# Test Repository\n\nFor integration testing.\n")

        # Initial commit
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_path, check=True, capture_output=True
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
        ["git", "commit", "-m", "Add spec"],
        cwd=test_repo, check=True, capture_output=True
    )

    return spec_path


def count_commits(repo_path: Path) -> int:
    """Count the number of commits in the repo."""
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return int(result.stdout.strip())


def get_commit_messages(repo_path: Path, count: int = 10) -> List[str]:
    """Get recent commit messages."""
    result = subprocess.run(
        ["git", "log", f"-{count}", "--format=%s"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n")


def file_exists(repo_path: Path, filename: str) -> bool:
    """Check if a file exists in the repo."""
    return (repo_path / filename).exists()


def get_file_content(repo_path: Path, filename: str) -> str:
    """Get content of a file in the repo."""
    return (repo_path / filename).read_text()
