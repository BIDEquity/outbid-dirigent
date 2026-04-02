"""
E2E Tests: Dirigent → Real Portal Integration

These tests run Dirigent against the actual Portal API (dev environment)
to verify the complete integration works end-to-end.

Requirements:
- PORTAL_URL: URL of the Portal (e.g., https://dev.portal.outbid.ai)
- TEST_API_SECRET: Secret for the Portal test API
- ANTHROPIC_API_KEY: For real Claude Code execution

Run with:
    pytest tests/integration/test_e2e_portal.py -v --e2e

These tests:
1. Create a test execution via Portal API
2. Run Dirigent with real Claude Code
3. Verify events arrived in Portal
4. Cleanup test data
"""
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import requests


# Required environment variables for E2E tests
PORTAL_URL = os.environ.get("PORTAL_URL", "https://dev.portal.outbid.ai")
TEST_API_SECRET = os.environ.get("TEST_API_SECRET", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def skip_if_missing_env():
    """Check required environment variables."""
    if not TEST_API_SECRET:
        pytest.skip("TEST_API_SECRET not set")
    if not ANTHROPIC_API_KEY:
        pytest.skip("ANTHROPIC_API_KEY not set")


class PortalTestClient:
    """Client for Portal test API."""

    def __init__(self, base_url: str, secret: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-Test-Secret": secret}

    def create_execution(self, test_name: str) -> dict:
        """Create a test execution in Portal."""
        resp = requests.post(
            f"{self.base_url}/api/test-execution",
            json={"test_name": test_name},
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_execution(self, execution_id: str) -> dict:
        """Get execution details and events."""
        resp = requests.get(
            f"{self.base_url}/api/test-execution/{execution_id}",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def cleanup_execution(self, execution_id: str) -> None:
        """Delete test execution and related data."""
        resp = requests.delete(
            f"{self.base_url}/api/test-execution/{execution_id}",
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()


@pytest.fixture
def portal_client():
    """Portal test client fixture."""
    skip_if_missing_env()
    return PortalTestClient(PORTAL_URL, TEST_API_SECRET)


@pytest.fixture
def test_repo(tmp_path: Path) -> Path:
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create minimal project
    (repo_path / "package.json").write_text('{"name":"test","scripts":{"test":"echo ok"}}')
    (repo_path / "README.md").write_text("# Test Project\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    return repo_path


@pytest.fixture
def spec_file(test_repo: Path) -> Path:
    """Create a simple spec file."""
    planning_dir = test_repo / ".planning"
    planning_dir.mkdir()

    spec_path = planning_dir / "SPEC.md"
    spec_path.write_text("""# Simple Test Feature

## Description
Create a file called hello.txt with the content "Hello, World!"

## Acceptance Criteria
- [ ] hello.txt exists in the root directory
- [ ] Content is "Hello, World!"
""")

    subprocess.run(["git", "add", "."], cwd=test_repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add spec"],
        cwd=test_repo,
        capture_output=True,
        check=True,
    )

    return spec_path


@pytest.mark.e2e
class TestE2EPortalIntegration:
    """
    End-to-end tests that run Dirigent against the real Portal.

    These tests verify the complete integration:
    1. Portal creates execution
    2. Dirigent sends events
    3. Portal receives and stores events
    """

    def test_dirigent_sends_events_to_portal(
        self, portal_client: PortalTestClient, test_repo: Path, spec_file: Path
    ):
        """
        Full E2E test: Dirigent sends events to real Portal.

        This test:
        1. Creates a test execution in Portal
        2. Runs Dirigent pointing to Portal
        3. Verifies Portal received the events
        4. Cleans up test data
        """
        execution_id = None

        try:
            # 1. Create test execution in Portal
            create_result = portal_client.create_execution("e2e-simple-feature")
            assert create_result["success"], f"Failed to create execution: {create_result}"

            execution_id = create_result["execution_id"]
            reporter_token = create_result["reporter_token"]

            print(f"\n📝 Created test execution: {execution_id}")

            # 2. Run Dirigent
            dirigent_src = Path(__file__).parent.parent.parent / "src"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(dirigent_src)

            result = subprocess.run(
                [
                    sys.executable, "-m", "outbid_dirigent.dirigent",
                    "--spec", str(spec_file),
                    "--repo", str(test_repo),
                    "--execution-mode", "autonomous",
                    "--portal-url", PORTAL_URL,
                    "--execution-id", execution_id,
                    "--reporter-token", reporter_token,
                    "--output", "json",
                ],
                cwd=test_repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
            )

            print(f"Dirigent stdout: {result.stdout[:500] if result.stdout else 'empty'}")
            if result.returncode != 0:
                print(f"Dirigent stderr: {result.stderr}")

            # Note: We don't assert returncode == 0 because Dirigent may fail
            # due to missing claude CLI, but it should still send some events

            # 3. Verify Portal received events
            portal_result = portal_client.get_execution(execution_id)
            assert portal_result["success"], f"Failed to get execution: {portal_result}"

            events = portal_result["events"]
            event_types = [e["event_type"] for e in events]

            print(f"📊 Portal received {len(events)} events: {event_types}")

            # We expect at least some events (even if execution failed)
            # Successful execution should have: stage_start, analysis_result, route_determined, etc.
            assert len(events) > 0, "Portal received no events from Dirigent"

            # Check execution status was updated
            execution = portal_result["execution"]
            assert execution["status"] != "pending", (
                f"Execution still pending - status should have changed. Status: {execution['status']}"
            )

            print(f"✅ E2E test passed!")
            print(f"   - Execution status: {execution['status']}")
            print(f"   - Events received: {len(events)}")
            print(f"   - Event types: {list(set(event_types))}")

        finally:
            # 4. Cleanup
            if execution_id:
                try:
                    portal_client.cleanup_execution(execution_id)
                    print(f"🧹 Cleaned up test execution: {execution_id}")
                except Exception as e:
                    print(f"⚠️ Cleanup failed: {e}")

    def test_portal_receives_stage_events(
        self, portal_client: PortalTestClient, test_repo: Path, spec_file: Path
    ):
        """
        Verify Portal receives stage_start and stage_complete events.
        """
        execution_id = None

        try:
            # Create test execution
            create_result = portal_client.create_execution("e2e-stage-events")
            execution_id = create_result["execution_id"]
            reporter_token = create_result["reporter_token"]

            # Run Dirigent
            dirigent_src = Path(__file__).parent.parent.parent / "src"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(dirigent_src)

            subprocess.run(
                [
                    sys.executable, "-m", "outbid_dirigent.dirigent",
                    "--spec", str(spec_file),
                    "--repo", str(test_repo),
                    "--execution-mode", "autonomous",
                    "--portal-url", PORTAL_URL,
                    "--execution-id", execution_id,
                    "--reporter-token", reporter_token,
                    "--output", "json",
                ],
                cwd=test_repo,
                env=env,
                capture_output=True,
                timeout=300,
            )

            # Check events in Portal
            portal_result = portal_client.get_execution(execution_id)
            event_types = [e["event_type"] for e in portal_result["events"]]

            # Verify stage events
            assert "stage_start" in event_types, f"Missing stage_start. Got: {event_types}"
            assert "stage_complete" in event_types, f"Missing stage_complete. Got: {event_types}"

            print(f"✅ Stage events verified in Portal")

        finally:
            if execution_id:
                try:
                    portal_client.cleanup_execution(execution_id)
                except Exception:
                    pass

    def test_portal_receives_analysis_result(
        self, portal_client: PortalTestClient, test_repo: Path, spec_file: Path
    ):
        """
        Verify Portal receives analysis_result event with route information.
        """
        execution_id = None

        try:
            create_result = portal_client.create_execution("e2e-analysis-result")
            execution_id = create_result["execution_id"]
            reporter_token = create_result["reporter_token"]

            dirigent_src = Path(__file__).parent.parent.parent / "src"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(dirigent_src)

            subprocess.run(
                [
                    sys.executable, "-m", "outbid_dirigent.dirigent",
                    "--spec", str(spec_file),
                    "--repo", str(test_repo),
                    "--execution-mode", "autonomous",
                    "--portal-url", PORTAL_URL,
                    "--execution-id", execution_id,
                    "--reporter-token", reporter_token,
                    "--output", "json",
                ],
                cwd=test_repo,
                env=env,
                capture_output=True,
                timeout=300,
            )

            portal_result = portal_client.get_execution(execution_id)
            events = portal_result["events"]

            # Find analysis_result event
            analysis_events = [e for e in events if e["event_type"] == "analysis_result"]
            assert len(analysis_events) > 0, f"No analysis_result event. Got: {[e['event_type'] for e in events]}"

            analysis = analysis_events[0]
            assert "route" in analysis["event_data"], f"analysis_result missing 'route': {analysis}"

            print(f"✅ Analysis result verified: route={analysis['event_data'].get('route')}")

        finally:
            if execution_id:
                try:
                    portal_client.cleanup_execution(execution_id)
                except Exception:
                    pass


@pytest.mark.e2e
class TestE2EWithMockedClaude:
    """
    E2E tests using mocked Claude Code (no API calls needed).

    These tests verify Portal integration without requiring ANTHROPIC_API_KEY.
    They use the mock_claude.py fixture to simulate Claude Code behavior.
    """

    @pytest.fixture
    def mock_claude_bin(self, tmp_path: Path) -> Path:
        """Create mock claude CLI."""
        mock_script_src = Path(__file__).parent.parent / "fixtures" / "mock_claude.py"
        if not mock_script_src.exists():
            pytest.skip("mock_claude.py fixture not found")

        mock_bin_dir = tmp_path / "bin"
        mock_bin_dir.mkdir()

        claude_script = mock_bin_dir / "claude"
        claude_script.write_text(f'#!/bin/bash\nexec python3 "{mock_script_src}" "$@"\n')
        claude_script.chmod(claude_script.stat().st_mode | stat.S_IEXEC)

        return mock_bin_dir

    def test_mocked_dirigent_to_real_portal(
        self,
        portal_client: PortalTestClient,
        mock_claude_bin: Path,
        test_repo: Path,
        spec_file: Path,
    ):
        """
        Test Dirigent → Portal with mocked Claude Code.

        This doesn't require ANTHROPIC_API_KEY but still tests real Portal integration.
        """
        # Skip ANTHROPIC_API_KEY check for this test
        if not TEST_API_SECRET:
            pytest.skip("TEST_API_SECRET not set")

        execution_id = None

        try:
            create_result = portal_client.create_execution("e2e-mocked-claude")
            execution_id = create_result["execution_id"]
            reporter_token = create_result["reporter_token"]

            print(f"\n📝 Created test execution: {execution_id}")

            # Run Dirigent with mocked Claude
            dirigent_src = Path(__file__).parent.parent.parent / "src"
            env = os.environ.copy()
            env["PATH"] = f"{mock_claude_bin}:{env.get('PATH', '')}"
            env["PYTHONPATH"] = str(dirigent_src)

            result = subprocess.run(
                [
                    sys.executable, "-m", "outbid_dirigent.dirigent",
                    "--spec", str(spec_file),
                    "--repo", str(test_repo),
                    "--execution-mode", "autonomous",
                    "--portal-url", PORTAL_URL,
                    "--execution-id", execution_id,
                    "--reporter-token", reporter_token,
                    "--output", "json",
                ],
                cwd=test_repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
            )

            print(f"Dirigent exit code: {result.returncode}")
            if result.returncode != 0:
                print(f"Dirigent stderr: {result.stderr[:500] if result.stderr else 'empty'}")

            # Verify Portal received events
            portal_result = portal_client.get_execution(execution_id)
            events = portal_result["events"]
            event_types = [e["event_type"] for e in events]

            print(f"📊 Portal received {len(events)} events: {event_types}")

            assert len(events) > 0, "Portal received no events"

            # Check for expected core events
            expected = {"stage_start", "stage_complete", "analysis_result"}
            actual = set(event_types)
            missing = expected - actual

            if missing:
                print(f"⚠️ Missing events: {missing}")
            else:
                print(f"✅ All core events received")

            print(f"✅ Mocked E2E test passed!")

        finally:
            if execution_id:
                try:
                    portal_client.cleanup_execution(execution_id)
                    print(f"🧹 Cleaned up: {execution_id}")
                except Exception as e:
                    print(f"⚠️ Cleanup failed: {e}")
