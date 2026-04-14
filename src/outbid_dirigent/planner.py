"""
Planner — creates execution plans via Claude Code.

Extracted from the Executor god class. Handles:
- Invoking /dirigent:create-plan via Claude Code subprocess
- Loading and validating the resulting PLAN.json
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.task_runner import TaskRunner
from outbid_dirigent.utils import strict_json_schema


class Planner:
    """Creates PLAN.json via Claude Code."""

    def __init__(self, repo_path: Path, spec_content: str, runner: TaskRunner, dirigent_dir: Optional[Path] = None):
        self.repo_path = repo_path
        self.spec_content = spec_content
        self.runner = runner
        self.dirigent_dir = dirigent_dir or (repo_path / ".dirigent")

    def create_plan(self) -> Optional[Plan]:
        """Generate PLAN.json via Claude Code. Returns Plan or None on failure."""

        # The /dirigent:create-plan skill reads all context from .dirigent/ files:
        #   - .dirigent/SPEC.md (written by Executor.__init__)
        #   - .dirigent/BUSINESS_RULES.md (from extract step)
        #   - .dirigent/CONTEXT.md (from quick-scan step)
        #   - .dirigent/test-harness.json (from init step)
        prompt = "Run /dirigent:create-plan"

        success, structured = self.runner._run_claude_structured(
            prompt,
            output_format={"type": "json_schema", "schema": strict_json_schema(Plan.model_json_schema())},
            timeout=1800,
        )
        if not success or structured is None:
            logger.error("Plan creation failed or returned no structured output")
            return None

        try:
            plan = Plan.model_validate(structured)
        except Exception as e:
            logger.error(f"Plan schema validation failed: {e}")
            return None

        plan_file = self.dirigent_dir / "PLAN.json"
        plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

        logger.info(f"Plan: {len(plan.phases)} phases, {plan.total_tasks} tasks")
        if plan.assumptions:
            logger.info(f"Assumptions: {len(plan.assumptions)}")
        if plan.out_of_scope:
            logger.info(f"Out of scope: {len(plan.out_of_scope)}")

        return plan
