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

import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

import re

from outbid_dirigent.contract_schema import Contract, Review, Verdict, FindingSeverity, CriterionVerdict, CriterionLayer
from outbid_dirigent.plan_schema import Plan, Phase

# Validation scripts bundled with the plugin skills
_PLUGIN_DIR = Path(__file__).parent / "plugin" / "skills"
_CONTRACT_VALIDATOR = _PLUGIN_DIR / "create-contract" / "scripts" / "validate_schema.py"
_REVIEW_VALIDATOR = _PLUGIN_DIR / "review-phase" / "scripts" / "validate_schema.py"


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

    def _contract_path(self, phase_id: str) -> Path:
        return self.contracts_dir / f"phase-{phase_id}.json"

    def _review_path(self, phase_id: str) -> Path:
        return self.reviews_dir / f"phase-{phase_id}.json"

    # ══════════════════════════════════════════
    # CONTRACT CREATION
    # ══════════════════════════════════════════

    MAX_SCHEMA_RETRIES = 2

    def create_contract(self, phase: Phase, plan: Plan, spec_content: str) -> bool:
        """Create acceptance criteria contract for a phase before execution.

        Runs a validation+retry loop: if the agent produces invalid JSON,
        the orchestrator feeds validation errors back for a targeted fix.
        """
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
            f"IMPORTANT: All dirigent artifacts are at $DIRIGENT_RUN_DIR={self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo). Read files from there and write output there."
        )
        success, _, stderr = self.runner._run_claude(prompt, timeout=300)

        if not success:
            logger.error(f"Contract creation failed for phase {phase.id}: {stderr[:200]}")
            return False

        # Validate with schema script + Pydantic, retry with error feedback
        for attempt in range(1, self.MAX_SCHEMA_RETRIES + 1):
            errors = self._run_validator(_CONTRACT_VALIDATOR, contract_path)
            if not errors:
                break
            logger.warning(
                f"Contract phase {phase.id} schema errors (attempt {attempt}): "
                + "; ".join(errors[:3])
            )
            fix_prompt = (
                f"The contract JSON at {contract_path} has schema errors. "
                f"Fix ONLY these errors and rewrite the file:\n"
                + "\n".join(f"- {e}" for e in errors)
            )
            self.runner._run_claude(fix_prompt, timeout=120)

        contract = Contract.load(contract_path)
        if contract is None:
            logger.error(f"Contract for phase {phase.id} was not created or is invalid JSON")
            return False

        self._validate_contract_quality(contract)

        logger.info(
            f"Contract created for phase {phase.id}: "
            f"{len(contract.acceptance_criteria)} criteria, "
            f"{len(contract.expected_files)} expected files"
        )
        return True

    @staticmethod
    def _run_validator(script: Path, target: Path) -> list[str]:
        """Run a validation script and return error lines. Empty list = valid."""
        if not script.exists() or not target.exists():
            return []
        try:
            result = subprocess.run(
                ["python3", str(script), str(target)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return []
            # Extract ERROR lines from output
            return [
                line.strip().removeprefix("ERROR: ").removeprefix("  ERROR: ")
                for line in result.stdout.splitlines()
                if "ERROR" in line
            ]
        except Exception as e:
            logger.debug(f"Validator failed: {e}")
            return []

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
            f"IMPORTANT: All dirigent artifacts are at $DIRIGENT_RUN_DIR={self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo). Read contract/harness from there, write review there."
        )

        success, _, stderr = self.runner._run_claude(prompt, timeout=600)

        if not success:
            logger.warning(f"Phase {phase.id} review subprocess failed: {stderr[:200]}")
            return "error"

        # Validate with schema script + retry with error feedback
        for attempt in range(1, self.MAX_SCHEMA_RETRIES + 1):
            errors = self._run_validator(_REVIEW_VALIDATOR, review_path)
            if not errors:
                break
            logger.warning(
                f"Phase {phase.id} review schema errors (attempt {attempt}): "
                + "; ".join(errors[:3])
            )
            fix_prompt = (
                f"The review JSON at {review_path} has schema errors. "
                f"Fix ONLY these errors and rewrite the file:\n"
                + "\n".join(f"- {e}" for e in errors)
            )
            self.runner._run_claude(fix_prompt, timeout=120)

        # Parse structured review
        review = Review.load(review_path)
        if review is None:
            logger.warning(f"Phase {phase.id} review: output missing or invalid JSON")
            return "error"

        # Reject pass verdicts where functional criteria lack evidence
        unproven = review.criteria_without_evidence
        if review.verdict == Verdict.PASS and unproven:
            logger.warning(
                f"Phase {phase.id} review claimed PASS but {len(unproven)} criteria "
                f"lack verification evidence — overriding to FAIL"
            )
            for cr in unproven:
                logger.warning(f"  No evidence: [{cr.ac_id}] {cr.notes[:100]}")
            review.verdict = Verdict.FAIL
            review.save(review_path)

        # Log structured results
        failed = review.failed_criteria
        critical = review.critical_count
        warn = review.warn_count

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
            f"IMPORTANT: All dirigent artifacts are at $DIRIGENT_RUN_DIR={self.dirigent_dir} "
            f"(NOT in .dirigent/ in the repo). Read review/contract from there."
        )
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
