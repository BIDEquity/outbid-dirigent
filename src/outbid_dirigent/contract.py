"""
Contract system — acceptance criteria for each phase.

Before a phase begins:
1. A contract is created (acceptance criteria both executor and reviewer agree on)
2. The executor works through the tasks
3. The reviewer checks against the contract and gives PASS/FAIL
4. On FAIL, the executor fixes issues
5. Iterate until PASS or max iterations reached
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Plan, Phase


class ContractManager:
    """Manages phase contracts and the review/fix iteration loop."""

    MAX_REVIEW_ITERATIONS = 3

    def __init__(self, repo_path: Path, runner):
        """
        Args:
            repo_path: Path to the target repository
            runner: TaskRunner instance for invoking Claude Code
        """
        self.repo_path = repo_path
        self.runner = runner
        self.dirigent_dir = repo_path / ".dirigent"
        self.contracts_dir = self.dirigent_dir / "contracts"
        self.reviews_dir = self.dirigent_dir / "reviews"
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    def _load_skill(self, skill_name: str) -> str:
        """Load a skill's SKILL.md content from the plugin directory."""
        skill_path = Path(__file__).parent / "plugin" / "skills" / skill_name / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return ""

    # ══════════════════════════════════════════
    # CONTRACT CREATION
    # ══════════════════════════════════════════

    def create_contract(self, phase: Phase, plan: Plan, spec_content: str) -> bool:
        """Create acceptance criteria contract for a phase before execution."""
        contract_file = self.contracts_dir / f"phase-{phase.id}-CONTRACT.md"

        # Skip if contract already exists
        if contract_file.exists():
            logger.info(f"Contract for phase {phase.id} already exists")
            return True

        skill_content = self._load_skill("create-contract")

        # Build task list for context
        task_list = "\n".join(
            f"- **{t.id}**: {t.name} — {t.description}\n"
            f"  Files to create: {', '.join(t.files_to_create) or 'none'}\n"
            f"  Files to modify: {', '.join(t.files_to_modify) or 'none'}"
            for t in phase.tasks
        )

        prompt = f"""<task>Create an acceptance criteria contract for Phase {phase.id} ("{phase.name}").</task>

<skill-instructions>
{skill_content}
</skill-instructions>

<phase>
<id>{phase.id}</id>
<name>{phase.name}</name>
<description>{phase.description}</description>
<tasks>
{task_list}
</tasks>
</phase>

<spec>
{spec_content[:3000]}
</spec>

<plan-context>
Title: {plan.title}
Total phases: {len(plan.phases)}
Assumptions: {', '.join(plan.assumptions) if plan.assumptions else 'none'}
</plan-context>

Create the contract file now at `.dirigent/contracts/phase-{phase.id}-CONTRACT.md`.
"""

        sys_prompt = "<role>Du erstellst Acceptance Criteria Contracts fuer Phasen. Sei praezise und messbar.</role>"

        success, _, stderr = self.runner._run_claude(
            prompt, timeout=300, system_prompt=sys_prompt,
        )

        if success and contract_file.exists():
            logger.info(f"Contract created for phase {phase.id}")
            return True

        logger.error(f"Contract creation failed for phase {phase.id}: {stderr[:200]}")
        return False

    # ══════════════════════════════════════════
    # REVIEW (reviewer role)
    # ══════════════════════════════════════════

    def review_phase(self, phase: Phase, plan: Plan, iteration: int = 1) -> str:
        """Review a completed phase against its contract.

        Returns: "pass", "fail", or "error"
        """
        skill_content = self._load_skill("review-phase")
        contract_file = self.contracts_dir / f"phase-{phase.id}-CONTRACT.md"

        contract_text = ""
        if contract_file.exists():
            contract_text = contract_file.read_text(encoding="utf-8")

        # Count commits for diff range
        commit_count = len(phase.tasks)

        # File list
        files_modified = []
        files_created = []
        for task in phase.tasks:
            files_modified.extend(task.files_to_modify)
            files_created.extend(task.files_to_create)
        all_files = sorted(set(files_modified + files_created))
        files_list = "\n".join(f"- {f}" for f in all_files) if all_files else "(see git diff)"

        review_file = self.reviews_dir / f"phase-{phase.id}-REVIEW.md"

        prompt = f"""<task>Review Phase {phase.id} ("{phase.name}") — Iteration {iteration}/{self.MAX_REVIEW_ITERATIONS}.</task>

<skill-instructions>
{skill_content}
</skill-instructions>

<contract>
{contract_text if contract_text else "No contract found — review based on task descriptions."}
</contract>

<review-scope>
<diff-command>git diff HEAD~{commit_count} --stat</diff-command>
<changed-files>
{files_list}
</changed-files>
</review-scope>

<phase-context>
Phase {phase.id}: {phase.name}
Description: {phase.description}
Tasks: {', '.join(t.name for t in phase.tasks)}
</phase-context>

Write your review to `.dirigent/reviews/phase-{phase.id}-REVIEW.md`.
The review MUST contain a clear "## Contract Verdict: PASS" or "## Contract Verdict: FAIL" line.
"""

        sys_prompt = """<role>Du bist ein Code-Reviewer. Du pruefst Aenderungen gegen den Contract.</role>
<constraints>
<constraint>Du bist NUR Reviewer. Aendere KEINEN Code.</constraint>
<constraint>Dein Verdict muss eindeutig PASS oder FAIL sein.</constraint>
<constraint>FAIL wenn auch nur ein Acceptance Criterion nicht erfuellt ist.</constraint>
</constraints>"""

        success, _, stderr = self.runner._run_claude(
            prompt, timeout=600, system_prompt=sys_prompt,
        )

        if not success:
            logger.warning(f"Phase {phase.id} review failed: {stderr[:200]}")
            return "error"

        if review_file.exists():
            content = review_file.read_text(encoding="utf-8")
            if "verdict: pass" in content.lower():
                logger.info(f"Phase {phase.id} review: PASS")
                return "pass"
            elif "verdict: fail" in content.lower():
                critical = content.lower().count("critical")
                warn = content.lower().count("warn")
                logger.info(f"Phase {phase.id} review: FAIL ({critical} critical, {warn} warnings)")
                return "fail"

        logger.info(f"Phase {phase.id} review: no clear verdict found, treating as pass")
        return "pass"

    # ══════════════════════════════════════════
    # FIX (executor role)
    # ══════════════════════════════════════════

    def fix_review_findings(self, phase: Phase, iteration: int = 1) -> bool:
        """Fix issues found during review (executor role).

        Returns True if fixes were applied successfully.
        """
        skill_content = self._load_skill("fix-review")
        review_file = self.reviews_dir / f"phase-{phase.id}-REVIEW.md"

        if not review_file.exists():
            logger.info(f"No review file for phase {phase.id}, nothing to fix")
            return True

        review_text = review_file.read_text(encoding="utf-8")

        # Skip if no actionable findings
        has_critical = "critical" in review_text.lower()
        has_warn = "warn" in review_text.lower()
        if not has_critical and not has_warn:
            logger.info(f"Phase {phase.id}: no CRITICAL/WARN findings, skipping fix")
            return True

        prompt = f"""<task>Fix review findings for Phase {phase.id} — Iteration {iteration}/{self.MAX_REVIEW_ITERATIONS}.</task>

<skill-instructions>
{skill_content}
</skill-instructions>

<review>
{review_text}
</review>

<instructions>
1. Read the review carefully
2. Fix all CRITICAL findings first, then WARN findings
3. Commit with: git add -A && git commit -m "fix(phase-{phase.id}): review fixes iteration {iteration}"
4. Write fixes report to .dirigent/reviews/phase-{phase.id}-FIXES.md
</instructions>
"""

        sys_prompt = f"""<role>Du bist der Executor. Fixe die Review-Findings.</role>
<constraints>
<constraint>Keine neuen Features — nur Fixes.</constraint>
<constraint>Jeder Fix muss minimal und fokussiert sein.</constraint>
</constraints>"""

        success, _, stderr = self.runner._run_claude(
            prompt, timeout=600, system_prompt=sys_prompt,
        )

        if success:
            logger.info(f"Phase {phase.id} fixes applied (iteration {iteration})")
            return True

        logger.warning(f"Phase {phase.id} fix failed: {stderr[:200]}")
        return False

    # ══════════════════════════════════════════
    # REVIEW/FIX ITERATION LOOP
    # ══════════════════════════════════════════

    def review_fix_loop(self, phase: Phase, plan: Plan) -> bool:
        """Run the review/fix iteration loop until PASS or max iterations.

        Flow:
        1. Reviewer reviews against contract → PASS/FAIL
        2. If FAIL: Executor fixes → go to 1
        3. If PASS or max iterations: done

        Returns True if the phase ultimately passed review.
        """
        for iteration in range(1, self.MAX_REVIEW_ITERATIONS + 1):
            logger.info(f"Phase {phase.id} review iteration {iteration}/{self.MAX_REVIEW_ITERATIONS}")

            verdict = self.review_phase(phase, plan, iteration)

            if verdict == "pass":
                logger.info(f"Phase {phase.id} passed review on iteration {iteration}")
                return True

            if verdict == "error":
                logger.warning(f"Phase {phase.id} review error on iteration {iteration}, continuing")
                return True  # Non-blocking: don't fail the whole run

            # verdict == "fail"
            if iteration >= self.MAX_REVIEW_ITERATIONS:
                logger.warning(
                    f"Phase {phase.id} failed review after {self.MAX_REVIEW_ITERATIONS} iterations, "
                    f"continuing anyway (non-blocking)"
                )
                return True  # Non-blocking but logged

            # Executor fixes
            fix_success = self.fix_review_findings(phase, iteration)
            if not fix_success:
                logger.warning(f"Phase {phase.id} fix failed on iteration {iteration}")
                # Continue to next review iteration anyway

        return True
