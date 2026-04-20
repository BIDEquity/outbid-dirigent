"""
Greenfield route smoke test.

Exercises the full greenfield pipeline against the fake claude binary:
  Scaffold → Plan → Execute (all tasks) → Review

Validates:
- Scaffold produces ARCHITECTURE.md, start.sh, test-harness.json
- Plan respects max 2 phases, max 7 tasks total
- Opinionated defaults flow from <key-patterns> into task prompts
- test-harness.json is available to planner and executor
- start.sh exists and is executable
- All phases pass review
"""

from pathlib import Path

from outbid_dirigent.router import Router, RouteType, StepType, mark_step_complete, load_state
from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.task_runner import TaskRunner
from outbid_dirigent.planner import Planner
from outbid_dirigent.contract import ContractManager
from outbid_dirigent.test_harness_schema import TestHarness


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


def _make_runner(repo: Path) -> TaskRunner:
    spec = (repo / "SPEC.md").read_text()
    return TaskRunner(repo_path=repo, spec_content=spec)


def _make_plan(repo: Path) -> Plan:
    runner = _make_runner(repo)
    planner = Planner(repo_path=repo, spec_content=(repo / "SPEC.md").read_text(), runner=runner)
    plan = planner.create_plan()
    assert plan is not None, "Planner returned None"
    return plan


# ═══════════════════════════════════════════════════════════════
# Route structure
# ═══════════════════════════════════════════════════════════════


class TestGreenfieldRoute:
    """Greenfield route starts with scaffold, has no init step."""

    def test_greenfield_steps_are_correct(self, tmp_path):
        router = Router(str(tmp_path))
        steps = router.GREENFIELD_STEPS
        step_types = [s.step_type for s in steps]

        assert StepType.INIT not in step_types, "Greenfield must not have init step"
        assert step_types[0] == StepType.GREENFIELD_SCAFFOLD, "Must start with scaffold"
        assert step_types[-1] == StepType.SHIP, "Must end with ship"
        assert StepType.PLANNING in step_types
        assert StepType.EXECUTION in step_types

    def test_greenfield_scaffold_is_required(self, tmp_path):
        router = Router(str(tmp_path))
        scaffold_step = router.GREENFIELD_STEPS[0]
        assert scaffold_step.required is True, "Scaffold step must be required"

    def test_route_detection_greenfield(self, tmp_path):
        router = Router(str(tmp_path))
        analysis = {
            "route": "greenfield",
            "route_reason": "new project",
            "estimated_scope": "small",
            "file_count": 5,
            "commit_count": 2,
        }
        route = router.determine_route(analysis)
        assert route.route_type == RouteType.GREENFIELD
        assert route.steps[0].step_type == StepType.GREENFIELD_SCAFFOLD


# ═══════════════════════════════════════════════════════════════
# Scaffold step
# ═══════════════════════════════════════════════════════════════


class TestGreenfieldScaffold:
    """Scaffold produces ARCHITECTURE.md, start.sh, test-harness.json."""

    def test_scaffold_creates_architecture_md(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        arch = repo / "ARCHITECTURE.md"
        assert arch.exists(), "Scaffold must create ARCHITECTURE.md"

    def test_scaffold_creates_start_sh(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        start_sh = repo / "start.sh"
        assert start_sh.exists(), "Scaffold must create start.sh"
        assert start_sh.stat().st_mode & 0o111, "start.sh must be executable"

    def test_scaffold_creates_test_harness(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        harness_path = repo / ".dirigent" / "test-harness.json"
        assert harness_path.exists(), "Scaffold must create test-harness.json"

        harness = TestHarness.load(harness_path)
        assert harness is not None, "test-harness.json must be valid"
        assert "test" in harness.commands, "Harness must have a test command"
        assert harness.portal is not None, "Harness must have portal config"
        assert harness.portal.port > 0, "Portal must have a port"

    def test_architecture_has_key_patterns_with_opinionated_defaults(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        arch_content = (repo / "ARCHITECTURE.md").read_text()

        assert "<key-patterns>" in arch_content
        assert "uv" in arch_content, "<key-patterns> must mention uv"
        assert "polars" in arch_content, "<key-patterns> must mention polars"
        assert "pydantic" in arch_content, "<key-patterns> must mention pydantic"
        assert "loguru" in arch_content, "<key-patterns> must mention loguru"

    def test_architecture_has_testing_verification(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        arch_content = (repo / "ARCHITECTURE.md").read_text()
        assert "<testing-verification>" in arch_content
        assert "pytest" in arch_content

    def test_architecture_has_architecture_decisions(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        arch_content = (repo / "ARCHITECTURE.md").read_text()
        assert "<architecture-decisions>" in arch_content

    def test_start_sh_binds_to_all_interfaces(self, fake_claude_env):
        repo = fake_claude_env
        runner = _make_runner(repo)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        content = (repo / "start.sh").read_text()
        assert "0.0.0.0" in content, "start.sh must bind to 0.0.0.0 for port-forwarding"


# ═══════════════════════════════════════════════════════════════
# Full greenfield flow
# ═══════════════════════════════════════════════════════════════


class TestGreenfieldFullFlow:
    """Full scaffold → plan → execute → review flow.

    Constraint: max 2 phases, max 7 tasks total.
    The fake claude produces 1 phase with 2 tasks, well within limits.
    """

    def test_scaffold_then_plan(self, fake_claude_env):
        """Scaffold produces artifacts, then plan reads them."""
        repo = fake_claude_env
        runner = _make_runner(repo)

        # Step 1: scaffold
        runner._run_claude("Run /dirigent:greenfield-scaffold")
        assert (repo / "ARCHITECTURE.md").exists()
        assert (repo / ".dirigent" / "test-harness.json").exists()

        # Step 2: plan
        plan = _make_plan(repo)
        assert plan.total_tasks >= 1
        assert len(plan.phases) <= 2, (
            f"Greenfield smoke test must not exceed 2 phases, got {len(plan.phases)}"
        )
        assert plan.total_tasks <= 7, (
            f"Greenfield smoke test must not exceed 7 tasks, got {plan.total_tasks}"
        )

    def test_scaffold_plan_execute(self, fake_claude_env):
        """Full flow: scaffold → plan → execute all tasks → review."""
        repo = fake_claude_env
        runner = _make_runner(repo)
        spec = (repo / "SPEC.md").read_text()

        # Scaffold
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        # Plan
        plan = _make_plan(repo)
        assert len(plan.phases) <= 2
        assert plan.total_tasks <= 7

        # Execute all tasks
        cm = ContractManager(repo_path=repo, runner=runner)
        for phase in plan.phases:
            cm.create_contract(phase, plan, spec)

            for task in phase.tasks:
                result = runner.run_task(task, plan, phase_num=int(phase.id))
                assert result.success, f"Task {task.id} failed: {result.summary}"
                assert result.commit_hash is not None, f"Task {task.id} must produce a commit"

            # Review
            verdict = cm.review_phase(phase, plan)
            assert verdict == "pass", f"Phase {phase.id} review failed"

    def test_opinionated_defaults_in_task_prompt(self, fake_claude_env):
        """Verify <key-patterns> from ARCHITECTURE.md appear in task prompts."""
        repo = fake_claude_env
        runner = _make_runner(repo)

        # Scaffold (writes ARCHITECTURE.md with <key-patterns>)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        # Plan
        plan = _make_plan(repo)
        task = plan.phases[0].tasks[0]

        # Build the prompt and check it includes opinionated defaults
        prompt = runner._build_prompt(task, plan)
        assert "key-patterns" in prompt, "Task prompt must include <key-patterns>"
        assert "uv" in prompt, "Task prompt must include opinionated defaults (uv)"

    def test_test_harness_in_task_prompt(self, fake_claude_env):
        """Verify test-harness.json content appears in task prompts."""
        repo = fake_claude_env
        runner = _make_runner(repo)

        # Scaffold (writes test-harness.json)
        runner._run_claude("Run /dirigent:greenfield-scaffold")

        # Plan
        plan = _make_plan(repo)
        task = plan.phases[0].tasks[0]

        prompt = runner._build_prompt(task, plan)
        assert "test-harness" in prompt, "Task prompt must include test-harness context"
        assert "pytest" in prompt, "Task prompt must include test command from harness"

    def test_state_tracking_through_greenfield_steps(self, fake_claude_env):
        """State correctly tracks greenfield-specific steps."""
        repo = fake_claude_env
        repo_str = str(repo)

        mark_step_complete(repo_str, "greenfield_scaffold")
        mark_step_complete(repo_str, "planning")

        state = load_state(repo_str)
        assert state is not None
        assert "greenfield_scaffold" in state["completed_steps"]
        assert "planning" in state["completed_steps"]
        assert "init" not in state["completed_steps"]
