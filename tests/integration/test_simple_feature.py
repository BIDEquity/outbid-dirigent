"""
Integration test: Simple Feature Execution

This test verifies the complete Dirigent flow:
1. Analyze repo
2. Create plan
3. Execute tasks (via Claude Code)
4. Create commits
5. Send events to portal

To run:
    # Fast mode (mocked Claude Code):
    pytest tests/integration/test_simple_feature.py -v

    # Real E2E mode (costs ~$0.50, requires ANTHROPIC_API_KEY):
    pytest tests/integration/test_simple_feature.py -v --e2e
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import (
    count_commits,
    file_exists,
    get_file_content,
)


class TestSimpleFeatureMocked:
    """
    Fast integration tests with mocked Claude Code execution.
    Tests the orchestration logic without API calls.
    """

    def test_mock_portal_receives_events(self, mock_portal, test_repo, spec_file):
        """Verify mock portal correctly captures events."""
        url, state = mock_portal

        # Set up pending execution
        state.pending_execution = {
            "execution_id": "test-exec-123",
            "reporter_token": "test-token-456",
        }

        # Simulate events that would be sent by Dirigent
        import requests

        # Simulate plan event
        requests.post(
            f"{url}/api/execution-event",
            json={
                "execution_id": "test-exec-123",
                "event": {
                    "type": "plan",
                    "ts": "2024-01-01T00:00:00Z",
                    "data": {"totalPhases": 1, "totalTasks": 1},
                },
            },
        )

        # Simulate task_start event
        requests.post(
            f"{url}/api/execution-event",
            json={
                "execution_id": "test-exec-123",
                "event": {
                    "type": "task_start",
                    "ts": "2024-01-01T00:00:01Z",
                    "data": {"taskId": "01-01", "name": "Test task"},
                },
            },
        )

        # Verify events captured
        assert len(state.events) == 2
        assert state.events[0].event_type == "plan"
        assert state.events[1].event_type == "task_start"

    def test_test_repo_fixture(self, test_repo):
        """Verify test repo is properly initialized."""
        assert test_repo.exists()
        assert (test_repo / "package.json").exists()
        assert (test_repo / ".git").exists()
        assert count_commits(test_repo) >= 1

    def test_spec_file_fixture(self, test_repo, spec_file):
        """Verify spec file is created correctly."""
        assert spec_file.exists()
        content = spec_file.read_text()
        assert "hello.txt" in content
        assert "Hello, World!" in content


@pytest.mark.e2e
class TestSimpleFeatureE2E:
    """
    Real end-to-end tests that run Claude Code.
    Requires ANTHROPIC_API_KEY and costs ~$0.50 per test.

    Run with: pytest tests/integration/ -v --e2e
    """

    @pytest.fixture(autouse=True)
    def check_api_key(self):
        """Skip if no API key available."""
        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

    def test_simple_feature_execution(self, mock_portal, test_repo, spec_file):
        """
        Full E2E test: Run Dirigent and verify it creates hello.txt

        This test:
        1. Starts mock portal
        2. Runs Dirigent with the simple spec
        3. Verifies hello.txt was created
        4. Verifies commits were made
        5. Verifies events were sent to portal
        """
        url, state = mock_portal
        initial_commits = count_commits(test_repo)

        # Set up pending execution (simulates portal trigger)
        state.pending_execution = {
            "execution_id": "e2e-test-001",
            "reporter_token": "e2e-token-001",
        }

        # Find dirigent entry point
        dirigent_src = Path(__file__).parent.parent.parent / "src"

        # Run Dirigent
        env = os.environ.copy()
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "outbid_dirigent.dirigent",
                "--spec",
                str(spec_file),
                "--repo",
                str(test_repo),
                "--execution-mode",
                "autonomous",
                "--portal-url",
                url,
                "--execution-id",
                "e2e-test-001",
                "--reporter-token",
                "e2e-token-001",
                "--output",
                "json",
            ],
            cwd=test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        # Debug output on failure
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

        # Assertions
        assert result.returncode == 0, f"Dirigent failed: {result.stderr}"

        # Verify hello.txt was created
        assert file_exists(test_repo, "hello.txt"), "hello.txt was not created"

        # Verify content (flexible - just check it exists and has content)
        content = get_file_content(test_repo, "hello.txt")
        assert len(content) > 0, "hello.txt is empty"

        # Verify commits were made
        final_commits = count_commits(test_repo)
        assert final_commits > initial_commits, "No new commits were made"

        # Verify portal received events
        assert len(state.events) > 0, "No events were sent to portal"

        # Check for expected event types
        event_types = [e.event_type for e in state.events]
        assert "plan" in event_types, "No plan event received"
        assert "task_start" in event_types, "No task_start event received"

        # Success!
        print("\n✅ E2E Test passed!")
        print(f"   - hello.txt created with content: {content[:50]}...")
        print(f"   - {final_commits - initial_commits} new commit(s)")
        print(f"   - {len(state.events)} event(s) sent to portal")

    def test_multi_task_execution(self, mock_portal, test_repo):
        """
        E2E test with multiple tasks.
        """
        url, state = mock_portal

        # Create a more complex spec
        planning_dir = test_repo / ".planning"
        planning_dir.mkdir(exist_ok=True)
        spec_path = planning_dir / "SPEC.md"
        spec_path.write_text("""# Multi-File Feature

## Beschreibung
Erstelle zwei Dateien:
1. `file1.txt` mit Inhalt "File 1"
2. `file2.txt` mit Inhalt "File 2"

## Akzeptanzkriterien
- [ ] file1.txt existiert
- [ ] file2.txt existiert
""")

        subprocess.run(["git", "add", "."], cwd=test_repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Add multi-file spec"],
            cwd=test_repo,
            check=True,
            capture_output=True,
        )

        state.pending_execution = {
            "execution_id": "e2e-test-002",
            "reporter_token": "e2e-token-002",
        }

        initial_commits = count_commits(test_repo)
        dirigent_src = Path(__file__).parent.parent.parent / "src"

        env = os.environ.copy()
        env["PYTHONPATH"] = str(dirigent_src)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "outbid_dirigent.dirigent",
                "--spec",
                str(spec_path),
                "--repo",
                str(test_repo),
                "--execution-mode",
                "autonomous",
                "--portal-url",
                url,
                "--execution-id",
                "e2e-test-002",
                "--reporter-token",
                "e2e-token-002",
                "--output",
                "json",
            ],
            cwd=test_repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )

        assert result.returncode == 0, f"Dirigent failed: {result.stderr}"
        assert file_exists(test_repo, "file1.txt"), "file1.txt not created"
        assert file_exists(test_repo, "file2.txt"), "file2.txt not created"

        final_commits = count_commits(test_repo)
        assert final_commits > initial_commits, "No new commits"

        print("\n✅ Multi-task E2E Test passed!")
        print(f"   - {final_commits - initial_commits} new commit(s)")
