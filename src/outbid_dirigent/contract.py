"""
Contract system — acceptance criteria for each phase.

Before a phase begins:
1. A contract is created (acceptance criteria both executor and reviewer agree on)
2. The executor works through the tasks
3. The reviewer checks against the contract and gives PASS/FAIL
4. On FAIL, the executor fixes issues
5. Iterate until PASS or max iterations reached

All prompts use /dirigent: slash commands that the subprocess Claude Code
resolves natively via the bundled plugin.
"""

from pathlib import Path

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

    # ══════════════════════════════════════════
    # CONTRACT CREATION
    # ══════════════════════════════════════════

    def create_contract(self, phase: Phase, plan: Plan, spec_content: str) -> bool:
        """Create acceptance criteria contract for a phase before execution."""
        contract_file = self.contracts_dir / f"phase-{phase.id}-CONTRACT.md"

        if contract_file.exists():
            logger.info(f"Contract for phase {phase.id} already exists")
            return True

        # Invoke /dirigent:create-contract with phase ID as argument.
        # The skill reads .dirigent/PLAN.json and .dirigent/SPEC.md from disk.
        prompt = f"Run /dirigent:create-contract {phase.id}"

        success, _, stderr = self.runner._run_claude(prompt, timeout=300)

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
        commit_count = len(phase.tasks)
        review_file = self.reviews_dir / f"phase-{phase.id}-REVIEW.md"

        # Invoke /dirigent:review-phase with phase ID, commit count, and iteration.
        # The skill reads the contract and runs git diff itself.
        prompt = f"Run /dirigent:review-phase {phase.id} --commits {commit_count} --iteration {iteration}"

        sys_prompt = (
            "You are a code reviewer. You check changes against the contract. "
            "You are ONLY the reviewer — do NOT change any code. "
            "Your verdict must be clearly PASS or FAIL."
        )

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

        # Invoke /dirigent:fix-review with phase ID and iteration.
        # The skill reads the review file from disk.
        prompt = f"Run /dirigent:fix-review {phase.id} --iteration {iteration}"

        success, _, stderr = self.runner._run_claude(prompt, timeout=600)

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
                return True  # Non-blocking

            # verdict == "fail"
            if iteration >= self.MAX_REVIEW_ITERATIONS:
                logger.warning(
                    f"Phase {phase.id} failed review after {self.MAX_REVIEW_ITERATIONS} iterations, "
                    f"continuing anyway (non-blocking)"
                )
                return True

            fix_success = self.fix_review_findings(phase, iteration)
            if not fix_success:
                logger.warning(f"Phase {phase.id} fix failed on iteration {iteration}")

        return True
