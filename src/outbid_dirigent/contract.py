"""
Contract system — acceptance criteria for each phase.

Before a phase begins:
1. A contract is created (acceptance criteria both executor and reviewer agree on)
2. The executor works through the tasks
3. The reviewer checks against the contract and gives PASS/FAIL
4. On FAIL, the executor fixes issues (reviewer never fixes directly)
5. Iterate until PASS or max iterations reached

Contracts and reviews are structured JSON files validated by Pydantic.
All prompts use /dirigent: slash commands resolved natively by the subprocess.
"""

from pathlib import Path
from typing import Optional

from loguru import logger

import re

from outbid_dirigent.contract_schema import Contract, Review, Verdict, FindingSeverity, CriterionVerdict, CriterionLayer
from outbid_dirigent.plan_schema import Plan, Phase
from outbid_dirigent.utils import strict_json_schema


class ContractManager:
    """Manages phase contracts and the review/fix iteration loop."""

    MAX_REVIEW_ITERATIONS = 3

    def __init__(self, repo_path: Path, runner, dirigent_dir: Optional[Path] = None):
        self.repo_path = repo_path
        self.runner = runner
        self.dirigent_dir = dirigent_dir or (repo_path / ".dirigent")
        self.contracts_dir = self.dirigent_dir / "contracts"
        self.reviews_dir = self.dirigent_dir / "reviews"
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        self.reviews_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize_phase_id(phase_id: str) -> str:
        """Normalize phase ID to zero-padded two-digit format.

        Handles various planner outputs: "1" -> "01", "01" -> "01",
        "phase-1" -> "01", "phase-01" -> "01".
        """
        # Strip "phase-" prefix if the planner included it
        cleaned = phase_id.removeprefix("phase-").removeprefix("phase_")
        try:
            return str(int(cleaned)).zfill(2)
        except (ValueError, TypeError):
            return str(phase_id)

    def _contract_path(self, phase_id: str) -> Path:
        return self.contracts_dir / f"phase-{self._normalize_phase_id(phase_id)}.json"

    def _review_path(self, phase_id: str) -> Path:
        return self.reviews_dir / f"phase-{self._normalize_phase_id(phase_id)}.json"

    # ══════════════════════════════════════════
    # CONTRACT CREATION
    # ══════════════════════════════════════════

    def create_contract(self, phase: Phase, plan: Plan, spec_content: str) -> bool:
        """Create acceptance criteria contract for a phase before execution."""
        contract_path = self._contract_path(phase.id)

        if contract_path.exists():
            contract = Contract.load(contract_path)
            if contract:
                logger.info(f"Contract for phase {phase.id} already exists "
                           f"({len(contract.acceptance_criteria)} criteria)")
                return True

        prompt = (
            f"Use the contract-negotiator agent to create an acceptance criteria "
            f"contract for phase {phase.id}. Pass it: phase_id={phase.id}\n\n"
            f"IMPORTANT: All dirigent artifacts are at {self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo). Read files from there."
        )
        success, structured = self.runner._run_claude_structured(
            prompt,
            output_format={"type": "json_schema", "schema": strict_json_schema(Contract.model_json_schema())},
            timeout=600,
        )
        if not success or structured is None:
            logger.error(f"Contract creation failed for phase {phase.id}")
            return False

        try:
            contract = Contract.model_validate(structured)
        except Exception as e:
            logger.error(f"Contract schema validation failed for phase {phase.id}: {e}")
            return False

        contract_path.write_text(contract.model_dump_json(indent=2), encoding="utf-8")
        self._validate_contract_quality(contract)

        logger.info(
            f"Contract created for phase {phase.id}: "
            f"{len(contract.acceptance_criteria)} criteria, "
            f"{len(contract.expected_files)} expected files"
        )

        # Send portal event (import here to avoid circular dependency)
        from outbid_dirigent.dirigent import get_portal_reporter
        reporter = get_portal_reporter()
        if reporter:
            reporter.contract_created(
                phase_id=phase.id,
                criteria_count=len(contract.acceptance_criteria),
                expected_files_count=len(contract.expected_files),
            )

        return True

    def load_contract(self, phase_id: str) -> Contract | None:
        """Load and validate a phase contract."""
        return Contract.load(self._contract_path(phase_id))

    # Patterns that indicate structural checks masquerading as behavioral criteria
    _GREP_PATTERNS = re.compile(
        r"\b(grep|rg|ag|ack)\b|"          # source code search
        r"\b(cat|head|tail)\s+\S+\.(py|ts|js|tsx|jsx|go|rs|java)\b|"  # reading source files
        r"\btest\s+-[fed]\b|"              # file existence checks
        r"\[\s*-[fed]\s+",                 # [ -f file ] checks
    )

    def _validate_contract_quality(self, contract: Contract):
        """Soft validation: warn about weak contract patterns. Never blocks."""
        criteria = contract.acceptance_criteria
        behavioral = [c for c in criteria if c.layer == CriterionLayer.BEHAVIORAL]
        boundary = [c for c in criteria if c.layer == CriterionLayer.BOUNDARY]

        total = len(criteria)
        behavioral_ratio = len(behavioral) / total if total else 0

        if not behavioral:
            logger.warning(
                f"Contract {contract.phase_id}: NO behavioral criteria — "
                f"contract tests structure, not user-facing behavior"
            )
        elif behavioral_ratio < 0.5:
            logger.warning(
                f"Contract {contract.phase_id}: only {len(behavioral)}/{total} criteria "
                f"are behavioral ({behavioral_ratio:.0%}) — should be >= 50%"
            )

        if not boundary:
            logger.warning(
                f"Contract {contract.phase_id}: no boundary criteria — "
                f"error paths and edge cases are untested"
            )

        # Check for grep-based verification in behavioral/boundary criteria
        for c in behavioral + boundary:
            if self._GREP_PATTERNS.search(c.verification):
                logger.warning(
                    f"Contract {contract.phase_id} [{c.id}]: behavioral/boundary criterion "
                    f"uses structural verification pattern: {c.verification[:80]}..."
                )

    # ══════════════════════════════════════════
    # REVIEW (reviewer role)
    # ══════════════════════════════════════════

    def review_phase(self, phase: Phase, plan: Plan, iteration: int = 1) -> str:
        """Review a completed phase against its contract.

        Returns: "pass", "fail", or "error"
        """
        commit_count = len(phase.tasks)
        review_path = self._review_path(phase.id)

        prompt = (
            f"Use the reviewer agent to review phase {phase.id}. "
            f"There are {commit_count} commits to review. This is iteration {iteration}.\n\n"
            f"IMPORTANT: All dirigent artifacts are at {self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo).\n"
            f"Read the contract from: {self._contract_path(phase.id)}"
        )
        success, structured = self.runner._run_claude_structured(
            prompt,
            output_format={"type": "json_schema", "schema": strict_json_schema(Review.model_json_schema())},
            timeout=1200,
        )
        if not success or structured is None:
            logger.warning(f"Phase {phase.id} review subprocess failed")
            return "error"

        try:
            review = Review.model_validate(structured)
        except Exception as e:
            logger.warning(f"Phase {phase.id} review schema error: {e}")
            return "error"

        review.save(review_path)

        # Warn about criteria that lack evidence but don't override the verdict.
        # The reviewer often executes verification commands (visible in logs) but
        # fails to populate the structured evidence arrays. Overriding PASS→FAIL
        # for missing evidence caused infinite review loops with no actionable fix.
        unproven = review.criteria_without_evidence
        if review.verdict == Verdict.PASS and unproven:
            logger.warning(
                f"Phase {phase.id} review: {len(unproven)} criteria lack structured "
                f"evidence (reviewer may have verified via tool calls without recording)"
            )
            for cr in unproven:
                logger.warning(f"  No evidence: [{cr.ac_id}] {cr.notes[:100]}")

        # Promote to PASS when all failures are infra-constrained (WARN only)
        if review.verdict == Verdict.FAIL and review.infra_constrained_only:
            warned = review.warned_criteria
            logger.info(
                f"Phase {phase.id} review: all {len(warned)} failing criteria are "
                f"infra-constrained (WARN) — promoting to PASS with caveat"
            )
            review.verdict = Verdict.PASS
            if not review.caveat:
                review.caveat = (
                    f"{len(warned)} criteria could not be verified due to infrastructure "
                    f"constraints: {', '.join(r.ac_id for r in warned)}"
                )
            review.save(review_path)

        # Log structured results
        failed = review.failed_criteria
        critical = review.critical_count
        warn = review.warn_count

        # Send portal event (import here to avoid circular dependency)
        from outbid_dirigent.dirigent import get_portal_reporter
        reporter = get_portal_reporter()
        if reporter:
            reporter.review_result(
                phase_id=phase.id,
                verdict="pass" if review.verdict == Verdict.PASS else "fail",
                iteration=iteration,
                passed_count=len(review.passed_criteria),
                failed_count=len(failed),
                critical_count=critical,
                warn_count=warn,
            )

        if review.verdict == Verdict.PASS:
            logger.info(
                f"Phase {phase.id} review: PASS "
                f"({len(review.passed_criteria)}/{len(review.criteria_results)} criteria passed, "
                f"{warn} warnings)"
            )
            return "pass"
        else:
            logger.info(
                f"Phase {phase.id} review: FAIL "
                f"({len(failed)} criteria failed, "
                f"{critical} critical, {warn} warnings)"
            )
            for cr in failed:
                logger.info(f"  FAIL [{cr.ac_id}]: {cr.notes[:100]}")
            return "fail"

    # ══════════════════════════════════════════
    # FIX (executor role)
    # ══════════════════════════════════════════

    def fix_review_findings(self, phase: Phase, iteration: int = 1) -> bool:
        """Fix issues found during review (executor role)."""
        review = Review.load(self._review_path(phase.id))

        if review is None:
            logger.info(f"No review for phase {phase.id}, nothing to fix")
            return True

        # Skip if no actionable findings
        if review.critical_count == 0 and review.warn_count == 0 and not review.failed_criteria:
            logger.info(f"Phase {phase.id}: no actionable findings, skipping fix")
            return True

        prompt = (
            f"Use the implementer agent to fix review findings for phase {phase.id}. "
            f"This is iteration {iteration}.\n\n"
            f"IMPORTANT: All dirigent artifacts are at {self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo).\n"
            f"Read the review from: {str(self._review_path(phase.id))}\n"
            f"Read the contract from: {str(self._contract_path(phase.id))}"
        )
        warned_ids = [r.ac_id for r in review.warned_criteria]
        if warned_ids:
            prompt += (
                f"\n\nDO NOT attempt to fix these infra-constrained criteria "
                f"(they failed due to missing environment/services, not code bugs): "
                f"{', '.join(warned_ids)}"
            )
        head_before = self.runner._get_latest_commit_hash()
        success, _, stderr = self.runner._run_claude(prompt, timeout=600)

        # Send portal event (import here to avoid circular dependency)
        from outbid_dirigent.dirigent import get_portal_reporter
        reporter = get_portal_reporter()
        if reporter:
            reporter.review_fix(
                phase_id=phase.id,
                iteration=iteration,
                success=success,
            )

        if success:
            # Auto-commit if the fix agent forgot to commit
            head_after = self.runner._get_latest_commit_hash()
            if head_after == head_before and self.runner._has_uncommitted_changes():
                logger.warning(f"Phase {phase.id} fix: agent did not commit — auto-committing")
                self.runner._auto_commit_msg(
                    f"fix(phase-{phase.id}): review fixes iteration {iteration}\n\n"
                    f"[auto-committed by dirigent — agent forgot to commit]"
                )
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
        2. If FAIL: Executor fixes findings (reviewer never fixes directly)
        3. Re-review → repeat until PASS or max iterations

        Returns True only if the phase actually passed review.
        Returns False if review failed after all iterations or errored repeatedly.
        """
        consecutive_errors = 0

        for iteration in range(1, self.MAX_REVIEW_ITERATIONS + 1):
            logger.info(f"Phase {phase.id} review iteration {iteration}/{self.MAX_REVIEW_ITERATIONS}")

            verdict = self.review_phase(phase, plan, iteration)

            if verdict == "pass":
                logger.info(f"Phase {phase.id} passed review on iteration {iteration}")
                return True

            if verdict == "error":
                consecutive_errors += 1
                logger.warning(f"Phase {phase.id} review error on iteration {iteration}")
                if consecutive_errors >= 2:
                    logger.error(
                        f"Phase {phase.id} review errored {consecutive_errors} times consecutively — "
                        f"treating as failure (review infrastructure unreliable)"
                    )
                    return False
                # Single error: retry on next iteration
                continue

            # verdict == "fail" — reset error counter since review worked
            consecutive_errors = 0

            if iteration >= self.MAX_REVIEW_ITERATIONS:
                logger.error(
                    f"Phase {phase.id} FAILED review after {self.MAX_REVIEW_ITERATIONS} iterations — "
                    f"blocking further execution"
                )
                return False

            fix_success = self.fix_review_findings(phase, iteration)
            if not fix_success:
                logger.warning(f"Phase {phase.id} fix failed on iteration {iteration}")

        return False
