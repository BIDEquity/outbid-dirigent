"""
Contract Tests: Portal ↔ Dirigent Integration

These tests verify the contract between the Portal and Dirigent:
1. Portal triggers execution with execution_id + reporter_token
2. Dirigent sends events: plan, task_start, commit, task_complete, progress, phase_complete, complete
3. Dirigent creates commits and branches

All tests use a mocked Claude Code, so they're FREE to run.
The real Dirigent code runs, only Claude API calls are mocked.

Run with:
    pytest tests/integration/test_portal_contract.py -v
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Generator

import pytest

from tests.conftest import (
    MockPortalState,
    PortalEvent,
    count_commits,
    get_commit_messages,
    file_exists,
)


@pytest.fixture
def mock_claude_bin(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a mock claude CLI script that simulates Claude Code.

    This script will be added to PATH so the Dirigent uses it
    instead of the real claude CLI.
    """
    # Copy mock_claude.py to a temp location
    mock_script_src = Path(__file__).parent.parent / "fixtures" / "mock_claude.py"
    mock_bin_dir = tmp_path / "bin"
    mock_bin_dir.mkdir()

    # Create a wrapper script named "claude" that calls our mock
    claude_script = mock_bin_dir / "claude"
    claude_script.write_text(f"""#!/bin/bash
exec python3 "{mock_script_src}" "$@"
""")
    claude_script.chmod(claude_script.stat().st_mode | stat.S_IEXEC)

    yield mock_bin_dir


@pytest.fixture
def contract_test_repo(tmp_path: Path) -> Path:
    """Create a test repo with a simple spec for contract testing."""
    repo_path = tmp_path / "contract-test-repo"
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
        "name": "contract-test-repo",
        "version": "1.0.0",
        "scripts": {"test": "echo 'ok'"}
    }
    (repo_path / "package.json").write_text(json.dumps(package_json, indent=2))
    (repo_path / "README.md").write_text("# Contract Test Repo\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path, check=True, capture_output=True
    )

    # Create spec
    planning_dir = repo_path / ".planning"
    planning_dir.mkdir()
    spec_content = """# Simple Feature Spec

## Beschreibung
Erstelle eine hello.txt Datei mit dem Inhalt "Hello, World!".

## Akzeptanzkriterien
- [ ] hello.txt existiert
- [ ] Inhalt ist "Hello, World!"
"""
    (planning_dir / "SPEC.md").write_text(spec_content)

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Add spec"],
        cwd=repo_path, check=True, capture_output=True
    )

    return repo_path


class TestPortalDirigentContract:
    """
    Contract tests verifying Portal ↔ Dirigent communication.

    These tests run the REAL Dirigent but with a MOCKED Claude Code,
    so they test the actual orchestration logic without API costs.
    """

    def test_dirigent_sends_plan_event(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent sends a 'plan' event to the portal."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        # Run dirigent with mock claude in PATH
        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"

        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-001",
                "--reporter-token", "contract-token-001",
                "--output", "json",
                "--phase", "execute",  # Don't try to push to remote
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Debug on failure
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        # Verify plan event was sent
        event_types = [e.event_type for e in state.events]
        assert "plan" in event_types, f"No plan event. Events: {event_types}"

        # Verify plan event structure
        plan_events = [e for e in state.events if e.event_type == "plan"]
        assert len(plan_events) >= 1
        plan_data = plan_events[0].data
        assert "totalPhases" in plan_data
        assert "totalTasks" in plan_data

    def test_dirigent_sends_task_lifecycle_events(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent sends task_start and task_complete events."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-002",
                "--reporter-token", "contract-token-002",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        event_types = [e.event_type for e in state.events]

        # Must have task lifecycle events
        assert "task_start" in event_types, f"No task_start. Events: {event_types}"
        assert "task_complete" in event_types, f"No task_complete. Events: {event_types}"

        # Verify task events have correct structure
        task_starts = [e for e in state.events if e.event_type == "task_start"]
        assert len(task_starts) >= 1
        assert "taskId" in task_starts[0].data
        assert "name" in task_starts[0].data

    def test_dirigent_sends_commit_events(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent sends commit events when tasks complete."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-003",
                "--reporter-token", "contract-token-003",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        event_types = [e.event_type for e in state.events]

        # Must have commit events
        assert "commit" in event_types, f"No commit event. Events: {event_types}"

        commit_events = [e for e in state.events if e.event_type == "commit"]
        assert len(commit_events) >= 1
        assert "hash" in commit_events[0].data
        assert "taskId" in commit_events[0].data

    def test_dirigent_sends_progress_events(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent sends progress events with completion percentage."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-004",
                "--reporter-token", "contract-token-004",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        event_types = [e.event_type for e in state.events]

        # Must have progress events
        assert "progress" in event_types, f"No progress event. Events: {event_types}"

        progress_events = [e for e in state.events if e.event_type == "progress"]
        assert len(progress_events) >= 1
        assert "percentComplete" in progress_events[0].data
        assert "tasksComplete" in progress_events[0].data
        assert "totalTasks" in progress_events[0].data

    def test_dirigent_sends_complete_event(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent sends a 'complete' event at the end."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-005",
                "--reporter-token", "contract-token-005",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        event_types = [e.event_type for e in state.events]

        # Must have complete event
        assert "complete" in event_types, f"No complete event. Events: {event_types}"

        complete_events = [e for e in state.events if e.event_type == "complete"]
        assert len(complete_events) == 1
        complete_data = complete_events[0].data
        assert "success" in complete_data
        assert "totalTasks" in complete_data
        assert "totalCommits" in complete_data

    def test_dirigent_creates_commits_in_repo(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """Verify Dirigent actually creates git commits."""
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"
        initial_commits = count_commits(contract_test_repo)

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-006",
                "--reporter-token", "contract-token-006",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        final_commits = count_commits(contract_test_repo)

        # Should have more commits than before
        assert final_commits > initial_commits, (
            f"No new commits. Before: {initial_commits}, After: {final_commits}"
        )

        # Verify commit messages contain task IDs
        messages = get_commit_messages(contract_test_repo, 5)
        task_commits = [m for m in messages if "feat(" in m or "Task" in m]
        assert len(task_commits) >= 1, f"No task commits found. Messages: {messages}"

    def test_full_event_sequence(
        self,
        mock_portal,
        mock_claude_bin: Path,
        contract_test_repo: Path,
    ):
        """
        Verify the complete event sequence matches what Portal expects.

        Expected sequence:
        1. plan
        2. phase_start
        3. task_start
        4. commit
        5. task_complete
        6. progress
        7. (repeat 3-6 for each task)
        8. phase_complete
        9. complete
        """
        url, state = mock_portal
        spec_path = contract_test_repo / ".planning" / "SPEC.md"

        env = os.environ.copy()
        env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
        dirigent_src = Path(__file__).parent.parent.parent / "src"
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable, "-m", "outbid_dirigent.dirigent",
                "--spec", str(spec_path),
                "--repo", str(contract_test_repo),
                "--execution-mode", "autonomous",
                "--portal-url", url,
                "--execution-id", "contract-test-007",
                "--reporter-token", "contract-token-007",
                "--output", "json",
                "--skip-ship",
            ],
            cwd=contract_test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )

        event_types = [e.event_type for e in state.events]

        # Verify all expected event types are present
        expected_types = {"plan", "phase_start", "task_start", "commit", "task_complete", "progress", "phase_complete", "complete"}
        actual_types = set(event_types)

        missing = expected_types - actual_types
        assert not missing, f"Missing event types: {missing}. Got: {event_types}"

        # Verify event order makes sense
        # plan should come before task_start
        plan_idx = event_types.index("plan")
        task_start_idx = event_types.index("task_start")
        assert plan_idx < task_start_idx, "plan should come before task_start"

        # complete should be last
        complete_idx = event_types.index("complete")
        assert complete_idx == len(event_types) - 1, "complete should be last event"

        print(f"\n✅ Full event sequence verified!")
        print(f"   Events received: {len(state.events)}")
        print(f"   Event types: {event_types}")
