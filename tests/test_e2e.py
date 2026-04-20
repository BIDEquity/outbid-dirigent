"""
E2E tests using the fake claude binary.

Exercises the real orchestration logic (Planner, TaskRunner, ContractManager)
against the deterministic fake claude, validating the full flow end-to-end.
"""

import json
from pathlib import Path


from outbid_dirigent.task_runner import TaskRunner
from outbid_dirigent.planner import Planner
from outbid_dirigent.contract import ContractManager
from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.router import mark_step_complete, get_next_step, load_state
from outbid_dirigent.analyzer import Analyzer, RepoAnalysis


# ═══════════════════════════════════════════════════════════════
# Greenfield flow tests
# ═══════════════════════════════════════════════════════════════


class TestE2EGreenfield:
    """Full greenfield flow against the fake claude binary."""

    def _make_runner(self, repo: Path, spec_content: str) -> TaskRunner:
        return TaskRunner(repo_path=repo, spec_content=spec_content)

    def _make_plan(self, repo: Path, spec_content: str) -> Plan:
        runner = self._make_runner(repo, spec_content)
        planner = Planner(repo_path=repo, spec_content=spec_content, runner=runner)
        plan = planner.create_plan()
        assert plan is not None, "Planner.create_plan() returned None"
        return plan

    def test_plan_creation_via_fake_claude(self, fake_claude_env):
        repo = fake_claude_env
        spec_content = (repo / "SPEC.md").read_text()

        plan = self._make_plan(repo, spec_content)

        assert plan.total_tasks >= 1
        assert plan.phases[0].id == "01"

    def test_task_execution_via_fake_claude(self, fake_claude_env):
        repo = fake_claude_env
        spec_content = (repo / "SPEC.md").read_text()
        runner = self._make_runner(repo, spec_content)
        plan = self._make_plan(repo, spec_content)

        task = plan.phases[0].tasks[0]
        result = runner.run_task(task, plan, phase_num=1)

        assert result.success is True
        assert result.commit_hash is not None
        summary_file = repo / ".dirigent" / "summaries" / f"{task.id}-SUMMARY.md"
        assert summary_file.exists()

    def test_contract_creation_via_fake_claude(self, fake_claude_env):
        repo = fake_claude_env
        spec_content = (repo / "SPEC.md").read_text()
        runner = self._make_runner(repo, spec_content)
        plan = self._make_plan(repo, spec_content)
        phase = plan.phases[0]

        cm = ContractManager(repo_path=repo, runner=runner)
        success = cm.create_contract(phase, plan, spec_content)

        assert success is True
        contract = cm.load_contract(phase.id)
        assert contract is not None
        assert len(contract.acceptance_criteria) >= 1

    def test_review_returns_pass_via_fake_claude(self, fake_claude_env):
        repo = fake_claude_env
        spec_content = (repo / "SPEC.md").read_text()
        runner = self._make_runner(repo, spec_content)
        plan = self._make_plan(repo, spec_content)
        phase = plan.phases[0]

        cm = ContractManager(repo_path=repo, runner=runner)
        cm.create_contract(phase, plan, spec_content)

        # Execute a task so there are changes to review
        task = phase.tasks[0]
        runner.run_task(task, plan, phase_num=1)

        verdict = cm.review_phase(phase, plan)
        assert verdict == "pass"

    def test_full_phase_flow(self, fake_claude_env):
        repo = fake_claude_env
        spec_content = (repo / "SPEC.md").read_text()
        runner = self._make_runner(repo, spec_content)
        plan = self._make_plan(repo, spec_content)
        phase = plan.phases[0]

        cm = ContractManager(repo_path=repo, runner=runner)
        cm.create_contract(phase, plan, spec_content)

        # Execute ALL tasks in the phase
        for task in phase.tasks:
            result = runner.run_task(task, plan, phase_num=1)
            assert result.success is True, f"Task {task.id} failed"

        # Review/fix loop should pass
        passed = cm.review_fix_loop(phase, plan)
        assert passed is True


# ═══════════════════════════════════════════════════════════════
# State tracking tests
# ═══════════════════════════════════════════════════════════════


class TestE2EStateTracking:
    """State tracking via router module functions."""

    def test_state_tracks_completed_steps(self, fake_claude_env):
        repo = fake_claude_env
        repo_str = str(repo)

        # Ensure .dirigent dir exists
        (repo / ".dirigent").mkdir(exist_ok=True)

        mark_step_complete(repo_str, "planning")
        mark_step_complete(repo_str, "execution")

        state = load_state(repo_str)
        assert state is not None
        assert "planning" in state["completed_steps"]
        assert "execution" in state["completed_steps"]

    def test_get_next_step_after_partial_completion(self, fake_claude_env):
        repo = fake_claude_env
        repo_str = str(repo)

        # Write a ROUTE.json manually with known steps
        route_data = {
            "route": "greenfield",
            "reason": "test",
            "steps": ["init", "planning", "execution", "ship"],
            "step_details": [
                {"type": "init", "name": "Init", "description": "Init", "required": True},
                {"type": "planning", "name": "Plan", "description": "Plan", "required": True},
                {"type": "execution", "name": "Exec", "description": "Exec", "required": True},
                {"type": "ship", "name": "Ship", "description": "Ship", "required": True},
            ],
            "estimated_tasks": 4,
            "oracle_needed": False,
            "repo_context_needed": False,
            "created_at": "2026-01-01T00:00:00",
        }
        dirigent_dir = repo / ".dirigent"
        dirigent_dir.mkdir(exist_ok=True)
        (dirigent_dir / "ROUTE.json").write_text(json.dumps(route_data), encoding="utf-8")

        # Complete first two steps
        mark_step_complete(repo_str, "init")
        mark_step_complete(repo_str, "planning")

        next_step = get_next_step(repo_str)
        assert next_step == "execution"


# ═══════════════════════════════════════════════════════════════
# Route selection tests
# ═══════════════════════════════════════════════════════════════


class TestE2ERouteSelection:
    """Route selection via Analyzer._determine_route with constructed dataclasses."""

    def test_legacy_spec_routes_to_legacy(self, git_repo):
        repo = git_repo
        spec_path = repo / "SPEC.md"
        spec_path.write_text(
            "# Refactor Legacy System\n\n"
            "Migrate the old codebase. Rewrite the billing module. "
            "Refactor the authentication layer.\n"
        )

        analyzer = Analyzer(repo_path=str(repo), spec_path=str(spec_path))

        repo_analysis = RepoAnalysis(
            repo_path=str(repo),
            repo_name="test-repo",
            primary_language="Ruby",
            secondary_languages=[],
            framework_detected=None,
            build_tool=None,
            commit_count=3000,
            last_commit_days_ago=400,
            last_commit_date=None,
            file_count=500,
            total_lines=100000,
            has_tests=True,
            has_ci=True,
            directories=[],
            config_files=[],
        )
        spec_analysis = analyzer._analyze_spec()

        route, reason, confidence, legacy_s, gf_s = analyzer._determine_route(
            repo_analysis, spec_analysis
        )
        assert route == "legacy", f"Expected legacy, got {route} (reason: {reason})"

    def test_tracking_spec_routes_to_tracking(self, git_repo):
        repo = git_repo
        spec_path = repo / "SPEC.md"
        spec_path.write_text(
            "# Add PostHog Analytics\n\n"
            "Implement event tracking across all user flows. "
            "Add PostHog initialization and user identification.\n"
        )

        analyzer = Analyzer(repo_path=str(repo), spec_path=str(spec_path))
        spec_analysis = analyzer._analyze_spec()

        repo_analysis = RepoAnalysis(
            repo_path=str(repo),
            repo_name="test-repo",
            primary_language="TypeScript",
            secondary_languages=[],
            framework_detected="Next.js",
            build_tool="npm",
            commit_count=200,
            last_commit_days_ago=5,
            last_commit_date=None,
            file_count=100,
            total_lines=20000,
            has_tests=True,
            has_ci=True,
            directories=[],
            config_files=[],
        )

        route, reason, confidence, legacy_s, gf_s = analyzer._determine_route(
            repo_analysis, spec_analysis
        )
        # Tracking route is disabled — should fall through to general routing
        assert route != "tracking", f"Tracking route should be disabled, got {route}"
