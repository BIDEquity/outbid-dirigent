"""
Outbid Dirigent – Executor (orchestrator)

Composes TaskRunner, Planner, and Shipper to execute the full pipeline.
Previously a 1300-line god class — now delegates to focused modules.
"""

import json
import re
import requests
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.analyzer import load_analysis
from outbid_dirigent.contract import ContractManager
from outbid_dirigent.infra_schema import InfraContext
from outbid_dirigent.init_phase import InitPhase
from outbid_dirigent.oracle import Oracle, create_oracle
from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.planner import Planner
from outbid_dirigent.progress import ProgressRenderer
from outbid_dirigent.proteus_integration import ProteusIntegration, create_proteus_integration
from outbid_dirigent.router import load_state, save_state, mark_step_complete
from outbid_dirigent.shipper import Shipper
from outbid_dirigent.task_runner import TaskRunner, TaskResult
from outbid_dirigent.utils import extract_phase_number


# ══════════════════════════════════════════════════════════════════════════════
# ANTHROPIC API PRICING (per million tokens, in USD)
# Source: https://platform.claude.com/docs/en/about-claude/pricing (March 2025)
# ══════════════════════════════════════════════════════════════════════════════
# Format: model_pattern -> (input_price_per_mtok, output_price_per_mtok)
# Cache pricing: reads = 0.1x input, writes = 1.25x input
CLAUDE_PRICING = {
    # Opus models
    "claude-opus-4-5": (5.0, 25.0),    # Opus 4.5/4.6
    "claude-4-opus": (15.0, 75.0),      # Opus 4/4.1
    # Sonnet models
    "claude-sonnet-4": (3.0, 15.0),     # Sonnet 4/4.5/4.6
    "claude-3-5-sonnet": (3.0, 15.0),   # Sonnet 3.5
    "claude-3-sonnet": (3.0, 15.0),     # Sonnet 3
    # Haiku models
    "claude-haiku-4": (1.0, 5.0),       # Haiku 4.5
    "claude-3-5-haiku": (0.80, 4.0),    # Haiku 3.5
    "claude-3-haiku": (0.25, 1.25),     # Haiku 3
}

# Fallback pricing if model not matched (use Sonnet pricing as reasonable default)
DEFAULT_PRICING = (3.0, 15.0)


def _get_model_pricing(model_id: str) -> tuple[float, float]:
    """Get pricing for a model ID.

    Returns (input_price_per_mtok, output_price_per_mtok).
    """
    if not model_id:
        return DEFAULT_PRICING

    model_lower = model_id.lower()

    # Try to match against known patterns
    for pattern, pricing in CLAUDE_PRICING.items():
        if pattern in model_lower:
            return pricing

    # Fallback based on model family
    if "opus" in model_lower:
        return CLAUDE_PRICING["claude-opus-4-5"]
    elif "sonnet" in model_lower:
        return CLAUDE_PRICING["claude-sonnet-4"]
    elif "haiku" in model_lower:
        return CLAUDE_PRICING["claude-3-5-haiku"]

    return DEFAULT_PRICING


class Executor:
    """Orchestrates the full dirigent execution pipeline.

    Delegates actual work to:
    - TaskRunner: runs individual Claude Code tasks
    - Planner: creates PLAN.json
    - Shipper: branch/push/PR
    """

    def __init__(
        self,
        repo_path: str,
        spec_path: str,
        dry_run: bool = False,
        use_proteus: bool = False,
        model: str = "",
        effort: str = "",
        portal_url: str = "",
        execution_id: str = "",
        reporter_token: str = "",
    ):
        self.repo_path = Path(repo_path).resolve()
        self.spec_path = Path(spec_path).resolve()
        self.use_proteus = use_proteus
        self.dry_run = dry_run
        self.oracle = create_oracle(str(self.repo_path))

        # Portal connection info
        self.portal_url = portal_url
        self.execution_id = execution_id
        self.reporter_token = reporter_token

        # Directories
        self.dirigent_dir = self.repo_path / ".dirigent"
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

        # Spec content — also write to .dirigent/SPEC.md so plugin skills can read it
        self.spec_content = self.spec_path.read_text(encoding="utf-8")
        spec_cache = self.dirigent_dir / "SPEC.md"
        spec_cache.write_text(self.spec_content, encoding="utf-8")

        # Compose modules
        self.runner = TaskRunner(
            repo_path=self.repo_path,
            spec_content=self.spec_content,
            default_model=model,
            default_effort=effort,
            portal_url=portal_url,
            execution_id=execution_id,
            reporter_token=reporter_token,
        )
        self.planner = Planner(
            repo_path=self.repo_path,
            spec_content=self.spec_content,
            runner=self.runner,
        )

        # Contract manager for review/fix iteration loop
        self.contract_manager = ContractManager(self.repo_path, self.runner)

        # Init phase handler
        self.init_phase = InitPhase(self.repo_path, self.runner)

        # Progress renderer
        self.progress = ProgressRenderer(self.repo_path)

        # Ship results (set by ship(), read by generate_summary())
        self.shipped_branch_name: Optional[str] = None
        self.shipped_pr_url: Optional[str] = None

        # Legacy logger bridge — keep the old logger working until fully migrated
        try:
            from outbid_dirigent.logger import get_logger
            self._legacy_logger = get_logger()
        except Exception:
            self._legacy_logger = None

    # ══════════════════════════════════════════
    # INIT PHASE
    # ══════════════════════════════════════════

    def run_init(self) -> bool:
        """Run init phase: discover and execute init scripts, detect e2e framework."""
        if self._legacy_logger:
            self._legacy_logger.info("Init Phase: Bootstrapping development environment")

        return self.init_phase.run()

    # ══════════════════════════════════════════
    # PROGRESS OUTPUT
    # ══════════════════════════════════════════

    def log_progress(self, fmt: str = "text"):
        """Log current progress in the specified format."""
        if fmt == "console":
            output = self.progress.console()
        elif fmt == "json":
            import json as _json
            output = _json.dumps(self.progress.to_json(), indent=2)
        else:
            output = self.progress.text()

        if self._legacy_logger:
            self._legacy_logger.info(output)
        else:
            logger.info(output)

    # ══════════════════════════════════════════
    # INCREASE TESTABILITY (Testability Route)
    # ══════════════════════════════════════════

    def increase_testability(self) -> bool:
        """Run testability analysis and produce recommendations."""
        logger.info("Running testability analysis...")
        prompt = "Run /dirigent:increase-testability"
        success, _, stderr = self.runner._run_claude(prompt, timeout=600)

        if not success:
            logger.error(f"Testability analysis failed: {stderr[:200]}")
            return False

        recs_file = self.dirigent_dir / "testability-recommendations.json"
        if recs_file.exists():
            import json as _json
            try:
                recs = _json.loads(recs_file.read_text(encoding="utf-8"))
                current = recs.get("current_score", "?")
                potential = recs.get("potential_score", "?")
                count = len(recs.get("recommendations", []))
                logger.info(f"Testability: {current}/10 → {potential}/10 ({count} recommendations)")
            except Exception:
                pass
            return True

        logger.warning("testability-recommendations.json was not created")
        return False

    # ══════════════════════════════════════════
    # ADD TRACKING (Tracking Route)
    # ══════════════════════════════════════════

    def add_tracking(self) -> bool:
        """Run PostHog tracking setup analysis."""
        logger.info("Running tracking setup analysis...")
        prompt = "Run /dirigent:add-posthog"
        success, _, stderr = self.runner._run_claude(prompt, timeout=600)

        if not success:
            logger.error(f"Tracking analysis failed: {stderr[:200]}")
            return False

        tracking_file = self.dirigent_dir / "tracking-plan.json"
        if tracking_file.exists():
            logger.info("Tracking plan created")
            return True

        logger.warning("tracking-plan.json was not created")
        return False

    # ══════════════════════════════════════════
    # ENTROPY MINIMIZATION (All Routes)
    # ══════════════════════════════════════════

    def entropy_minimization(self) -> bool:
        """Run entropy minimization to align docs, remove dead code, resolve contradictions."""
        logger.info("Running entropy minimization...")
        prompt = "Run /dirigent:entropy-minimization"
        success, stdout, stderr = self.runner._run_claude(prompt, timeout=900)

        if not success:
            logger.error(f"Entropy minimization failed: {stderr[:200]}")
            return False

        report_file = self.dirigent_dir / "entropy-report.json"
        if report_file.exists():
            import json as _json
            try:
                report = _json.loads(report_file.read_text(encoding="utf-8"))
                fixed = report.get("issues_fixed", 0)
                remaining = report.get("issues_remaining", 0)
                logger.info(f"Entropy minimization: {fixed} issues fixed, {remaining} remaining")
            except Exception:
                pass
            return True

        # No report file is OK — the agent may have found nothing to fix
        logger.info("Entropy minimization complete (no report generated — repo may be clean)")
        return True

    # ══════════════════════════════════════════
    # BUSINESS RULE EXTRACTION (Legacy Route)
    # ══════════════════════════════════════════

    def extract_business_rules(self) -> bool:
        """Extract business rules from the codebase (Legacy route)."""
        if self._legacy_logger:
            self._legacy_logger.extract_start()

        if self.use_proteus:
            return self._extract_with_proteus()

        # Primary language from analysis
        analysis_file = self.dirigent_dir / "ANALYSIS.json"
        language = "unbekannt"
        if analysis_file.exists():
            with open(analysis_file, encoding="utf-8") as f:
                language = json.load(f).get("primary_language", "unbekannt")

        # Invoke the skill natively — it reads context from disk
        prompt = f"Run /dirigent:extract-business-rules {language}"

        success, _, stderr = self.runner._run_claude(prompt, timeout=900)
        if not success:
            logger.error(f"Business Rule extraction failed: {stderr}")
            return False

        rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        if rules_file.exists():
            content = rules_file.read_text(encoding="utf-8")
            rule_count = content.count("- ") + content.count("* ")
            if self._legacy_logger:
                self._legacy_logger.extract_done(rule_count)
            logger.info(f"Business Rules extracted ({rule_count} rules)")
            return True

        logger.error("BUSINESS_RULES.md was not created")
        return False

    def _extract_with_proteus(self) -> bool:
        """Use Proteus for deep domain extraction."""
        logger.info("Using Proteus for domain extraction...")
        proteus = create_proteus_integration(str(self.repo_path), self.dry_run)

        if not proteus.run_full_extraction():
            logger.error("Proteus extraction failed")
            return False

        summary = proteus.get_extraction_summary()
        logger.info(
            f"Proteus: {summary['fields_count']} Fields, "
            f"{summary['rules_count']} Rules, "
            f"{summary['events_count']} Events, "
            f"{summary['dependencies_count']} Dependencies"
        )
        self._create_business_rules_from_proteus(proteus)
        return True

    def _create_business_rules_from_proteus(self, proteus: ProteusIntegration):
        """Create BUSINESS_RULES.md from Proteus data."""
        proteus_dir = self.repo_path / ".proteus"
        parts = [f"# Business Rules – {self.repo_path.name}\n", "*Extracted via Proteus*\n"]

        arch_file = proteus_dir / "arch.md"
        if arch_file.exists():
            parts.extend(["## Architektur\n", arch_file.read_text(encoding="utf-8")[:3000], "\n"])

        for name, section in [("rules.json", "Business Rules"), ("events.json", "Domain Events")]:
            fpath = proteus_dir / name
            if fpath.exists():
                try:
                    with open(fpath) as f:
                        data = json.load(f)
                    key = "rules" if "rules" in name else "events"
                    parts.append(f"\n## {section}\n")
                    for item in data.get(key, []):
                        parts.append(f"- **{item.get('name', 'Unknown')}**: {item.get('description', item.get('trigger', ''))}\n")
                except Exception:
                    pass

        rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        rules_file.write_text("".join(parts), encoding="utf-8")
        logger.info("BUSINESS_RULES.md created from Proteus data")

    # ══════════════════════════════════════════
    # QUICK SCAN (Hybrid Route)
    # ══════════════════════════════════════════

    def quick_scan(self) -> bool:
        """Quick scan of relevant files (Hybrid route)."""
        logger.info("Starting Quick Scan...")
        # Invoke the skill natively — it reads .dirigent/SPEC.md from disk
        prompt = "Run /dirigent:quick-scan"
        success, _, stderr = self.runner._run_claude(prompt, timeout=300)
        if not success:
            logger.error(f"Quick Scan failed: {stderr}")
            return False
        logger.info("Quick Scan complete")
        return True

    # ══════════════════════════════════════════
    # PLANNING
    # ══════════════════════════════════════════

    def create_plan(self) -> bool:
        """Create the execution plan via Claude Code."""
        if self._legacy_logger:
            self._legacy_logger.plan_start()

        plan = self.planner.create_plan()
        if plan is None:
            return False

        if self._legacy_logger:
            # Include full task details for portal display
            phase_details = [
                {
                    "phase": p.id,
                    "name": p.name,
                    "description": p.description,
                    "taskCount": len(p.tasks),
                    "tasks": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "description": t.description,
                        }
                        for t in p.tasks
                    ],
                }
                for p in plan.phases
            ]
            self._legacy_logger.plan_done(len(plan.phases), plan.total_tasks, phase_details)
        return True

    # ══════════════════════════════════════════
    # PLAN EXECUTION
    # ══════════════════════════════════════════

    def execute_plan(self) -> bool:
        """Execute all tasks in the plan sequentially."""
        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        if not plan:
            logger.error("No plan found")
            return False

        state = self._load_or_init_state()

        total_phases = len(plan.phases)
        total_tasks = plan.total_tasks

        # Interactive mode check
        from outbid_dirigent.dirigent import get_questioner, get_execution_mode
        questioner = get_questioner()
        execution_mode = get_execution_mode()

        if execution_mode == "interactive" and questioner and questioner.is_active():
            result = questioner.ask(
                question=f"Der Plan enthält {total_phases} Phasen mit {total_tasks} Tasks. Soll die Ausführung gestartet werden?",
                options=["Ja, starten", "Nein, abbrechen"],
                context=f"Geschätzte Zeit: {total_tasks * 5} Minuten.",
                phase=0,
            )
            if result.answered and result.answer and ("abbrechen" in result.answer.lower() or "nein" in result.answer.lower()):
                logger.info("Execution cancelled by user")
                return False
        else:
            if self._legacy_logger:
                self._legacy_logger.info(f"Starte Ausführung: {total_phases} Phasen, {total_tasks} Tasks")

        for phase in plan.phases:
            if phase.id in state.get("completed_phases", []):
                logger.info(f"Phase {phase.id} already completed, skipping")
                continue

            # Create contract (acceptance criteria) before phase execution
            contract_ok = self._create_phase_contract(phase, plan)
            if contract_ok:
                logger.info(f"Phase {phase.id} contract created")
            else:
                logger.warning(f"Phase {phase.id} contract creation failed (non-blocking)")

            if self._legacy_logger:
                self._legacy_logger.phase_start(phase.id, phase.name, len(phase.tasks))

            phase_deviation_count = 0
            phase_commit_count = 0
            phase_tasks_completed = 0

            for task in phase.tasks:
                if task.id in state.get("completed_tasks", []):
                    logger.info(f"Task {task.id} already completed, skipping")
                    phase_tasks_completed += 1
                    continue

                if self._legacy_logger:
                    self._legacy_logger.task_start(task.id, task.name, phase=extract_phase_number(phase.id))

                result = self.runner.run_task(task, plan, phase_num=phase.id)

                if result.success:
                    state["completed_tasks"].append(task.id)
                    save_state(str(self.repo_path), state)
                    phase_tasks_completed += 1
                    phase_deviation_count += len(result.deviations)
                    if result.commit_hash:
                        phase_commit_count += 1

                    if self._legacy_logger:
                        for dev in result.deviations:
                            self._legacy_logger.deviation(dev["type"], dev["description"], task_id=task.id, phase=extract_phase_number(phase.id))
                        self._legacy_logger.task_done(task.id, result.commit_hash, task_name=task.name, phase=extract_phase_number(phase.id))
                else:
                    state.setdefault("failed_tasks", []).append({
                        "task_id": task.id,
                        "error": result.summary,
                        "attempts": result.attempts,
                    })
                    save_state(str(self.repo_path), state)

                    logger.error(f"Task {task.id} failed after {result.attempts} attempts")
                    if self._legacy_logger:
                        self._legacy_logger.stop(f"Task {task.id} fehlgeschlagen nach {result.attempts} Versuchen")
                        self._legacy_logger.run_complete(success=False)
                    return False

            # Phase review — code review + fix cycle (blocks on failure)
            review_passed = self._review_phase(phase, plan)
            if not review_passed:
                state.setdefault("failed_phases", []).append({
                    "phase_id": phase.id,
                    "reason": "review_failed",
                })
                save_state(str(self.repo_path), state)
                logger.error(
                    f"Phase {phase.id} review failed — halting execution. "
                    f"Fix issues and --resume to retry."
                )
                if self._legacy_logger:
                    self._legacy_logger.stop(f"Phase {phase.id} review failed")
                    self._legacy_logger.run_complete(success=False)
                return False

            # Phase complete
            state.setdefault("completed_phases", []).append(phase.id)
            save_state(str(self.repo_path), state)
            if self._legacy_logger:
                self._legacy_logger.phase_complete(
                    phase.id, phase.name, phase_tasks_completed,
                    phase_deviation_count, phase_commit_count,
                )

        if self._legacy_logger:
            self._legacy_logger.run_complete(success=True)
        return True

    def _load_or_init_state(self) -> dict:
        state = load_state(str(self.repo_path))
        if not state:
            state = {
                "started_at": datetime.now().isoformat(),
                "completed_phases": [],
                "completed_tasks": [],
            }
        else:
            state.setdefault("completed_phases", [])
            state.setdefault("completed_tasks", [])
        save_state(str(self.repo_path), state)
        return state

    # ══════════════════════════════════════════
    # CONTRACT + PHASE REVIEW (review/fix loop)
    # ══════════════════════════════════════════

    def _create_phase_contract(self, phase, plan: Plan) -> bool:
        """Create acceptance criteria contract before a phase begins."""
        return self.contract_manager.create_contract(phase, plan, self.spec_content)

    def _review_phase(self, phase, plan: Plan) -> bool:
        """Run the contract-based review/fix iteration loop.

        Flow:
        1. Reviewer reviews changes against the phase contract → PASS/FAIL
        2. If FAIL: Executor fixes the findings (reviewer never fixes directly)
        3. Re-review until PASS or max iterations reached

        Returns True if passed, False if failed. Failure blocks execution.
        """
        commit_count = len(phase.tasks)
        if commit_count == 0:
            return True

        logger.info(f"Phase {phase.id} review: contract-based review/fix loop")
        passed = self.contract_manager.review_fix_loop(phase, plan)

        # Log progress after review
        self.log_progress("text")

        from outbid_dirigent.contract_schema import Review
        review = Review.load(self.dirigent_dir / "reviews" / f"phase-{phase.id}.json")

        if passed and review:
            logger.info(
                f"Phase {phase.id} review: {review.verdict.value.upper()} "
                f"({review.critical_count} critical, {review.warn_count} warnings, "
                f"{len(review.criteria_results)} criteria evaluated)"
            )
        elif passed:
            logger.info(f"Phase {phase.id} review: no structured review created")
        else:
            logger.error(f"Phase {phase.id} review FAILED — blocking execution")
            if review:
                for cr in review.failed_criteria:
                    logger.error(f"  FAIL [{cr.ac_id}]: {cr.notes[:200]}")

        return passed

    # ══════════════════════════════════════════
    # TEST STEP
    # ══════════════════════════════════════════

    def run_tests(self) -> bool:
        """Run verification commands from the test harness. Returns True if passed or no harness."""
        from outbid_dirigent.test_harness_schema import TestHarness

        harness = TestHarness.load(self.dirigent_dir / "test-harness.json")
        if not harness or not harness.verification_commands:
            logger.info("No test harness or verification commands, skipping test step")
            return True

        logger.info(f"Running {len(harness.verification_commands)} verification commands...")
        import subprocess as sp
        all_passed = True

        for cmd in harness.verification_commands:
            try:
                result = sp.run(
                    ["bash", "-c", cmd.command],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=120,
                )
                if result.returncode == 0:
                    logger.info(f"  PASS: {cmd.name}")
                else:
                    logger.error(f"  FAIL: {cmd.name} (exit {result.returncode})")
                    if result.stderr:
                        logger.error(f"    stderr: {result.stderr[:200]}")
                    all_passed = False
            except sp.TimeoutExpired:
                logger.error(f"  TIMEOUT: {cmd.name}")
                all_passed = False
            except Exception as e:
                logger.error(f"  ERROR: {cmd.name}: {e}")
                all_passed = False

        # Also run e2e framework suite if configured
        if harness.e2e_framework.run_command and harness.e2e_framework.framework != "none":
            logger.info(f"Running e2e suite: {harness.e2e_framework.run_command}")
            try:
                result = sp.run(
                    ["bash", "-c", harness.e2e_framework.run_command],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=600,
                )
                if result.returncode == 0:
                    logger.info("  E2e suite: PASS")
                else:
                    logger.error(f"  E2e suite: FAIL (exit {result.returncode})")
                    all_passed = False
            except Exception as e:
                logger.error(f"  E2e suite error: {e}")
                all_passed = False

        if all_passed:
            logger.info("All verification commands passed")
        else:
            logger.error("Verification failed — blocking ship")

        # Attach infra context to test harness result
        infra_ctx = InfraContext.load(self.dirigent_dir / "infra-context.json")
        if infra_ctx:
            logger.info(f"Test confidence: {infra_ctx.confidence} (tier: {infra_ctx.tier.value})")

        # Wire testing_complete() to portal reporter
        from outbid_dirigent.dirigent import get_portal_reporter
        reporter = get_portal_reporter()
        if reporter and hasattr(reporter, "testing_complete"):
            reporter.testing_complete(str(self.repo_path))

        return all_passed

    # ══════════════════════════════════════════
    # SHIPPING
    # ══════════════════════════════════════════

    def ship(self) -> bool:
        """Create branch, push, and open PR."""
        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        if self._legacy_logger:
            self._legacy_logger.ship_start("dirigent/...")

        shipper = Shipper(self.repo_path, plan, self.dry_run)
        success = shipper.ship()

        self.shipped_branch_name = shipper.branch_name
        self.shipped_pr_url = shipper.pr_url

        if self._legacy_logger:
            if shipper.pr_url:
                self._legacy_logger.ship_done(shipper.pr_url)
            elif shipper.branch_name:
                self._legacy_logger.ship_pushed(shipper.branch_name)
        return success

    # ══════════════════════════════════════════
    # SUMMARY GENERATION
    # ══════════════════════════════════════════

    def generate_summary(self, branch_name: str = None, pr_url: str = None) -> dict:
        """Generate the final execution report."""
        logger.info("Generating summary...")

        plan = Plan.load(self.dirigent_dir / "PLAN.json")
        plan_title = plan.title if plan else "Feature"

        summaries = [f.read_text(encoding="utf-8") for f in sorted(self.summaries_dir.glob("*-SUMMARY.md"))]
        decisions = self.oracle.get_all_decisions()
        files_changed = self._get_files_changed()
        deviations = self._collect_all_deviations(summaries)

        cost_totals = self._legacy_logger.get_cost_totals() if self._legacy_logger else {
            "total_cost_cents": 0, "total_input_tokens": 0, "total_output_tokens": 0,
        }

        if not branch_name:
            branch_name = self.shipped_branch_name or self._get_current_branch()
        if not pr_url:
            pr_url = self.shipped_pr_url

        # Extract test instructions and manual hints for the summary
        test_instructions = self._extract_test_instructions()
        manual_hints = self._generate_manual_test_hints(files_changed)

        markdown = self._generate_summary_markdown(
            plan_title, plan, summaries, decisions, files_changed, deviations, cost_totals
        )

        # NOTE: We no longer call _legacy_logger.summary() here because:
        # 1. It sends a summary event with cost_totals from legacy logger (which doesn't track transcripts)
        # 2. _send_summary_to_portal() collects token usage directly from Claude Code transcripts
        # 3. The daemon would forward the legacy event first, causing the portal to reject our accurate one

        self._send_summary_to_portal(
            markdown, files_changed, decisions, deviations, branch_name, pr_url,
            test_instructions, manual_hints
        )

        return {"markdown": markdown, "files_changed": files_changed, "decisions": decisions,
                "deviations": deviations, "cost_totals": cost_totals, "branch_name": branch_name, "pr_url": pr_url}

    # ── Summary helpers ──

    def _get_current_branch(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path, capture_output=True, text=True, timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_files_changed(self) -> list[dict]:
        """Get files changed during this execution only.

        Uses the state's started_at timestamp to find the first commit
        of this execution, then diffs from there to HEAD.
        """
        try:
            # Load state to get execution start time
            state = load_state(str(self.repo_path))
            started_at = state.get("started_at") if state else None

            if started_at:
                # Find commits made after the execution started
                # Use --since to get only commits from this execution
                result = subprocess.run(
                    ["git", "log", "--since", started_at, "--format=%H", "--reverse"],
                    cwd=self.repo_path, capture_output=True, text=True, timeout=30,
                )
                commits = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]

                if commits:
                    # Get the first commit of this execution
                    first_commit = commits[0]
                    # Diff from parent of first commit to HEAD
                    diff_cmd = ["git", "diff", "--numstat", f"{first_commit}^..HEAD"]
                else:
                    # No commits in this execution
                    return []
            else:
                # Fallback: use completed_tasks count as proxy for commit count
                completed_tasks = len(state.get("completed_tasks", [])) if state else 0
                commit_count = max(1, completed_tasks + 2)  # +2 for review commits
                diff_cmd = ["git", "diff", "--numstat", f"HEAD~{commit_count}..HEAD"]

            result = subprocess.run(
                diff_cmd,
                cwd=self.repo_path, capture_output=True, text=True, timeout=30,
            )
            files = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split("\t") if line else []
                if len(parts) == 3:
                    files.append({
                        "path": parts[2],
                        "lines_added": int(parts[0]) if parts[0] != '-' else 0,
                        "lines_removed": int(parts[1]) if parts[1] != '-' else 0,
                    })
            return files
        except Exception as e:
            logger.debug(f"Error getting files changed: {e}")
            return []

    def _collect_all_deviations(self, summaries: list[str]) -> list[dict]:
        all_devs = []
        for s in summaries:
            all_devs.extend(TaskRunner._extract_deviations(s))
        return all_devs

    def _generate_summary_markdown(
        self, title: str, plan: Optional[Plan], summaries: list[str],
        decisions: list[dict], files: list[dict], deviations: list[dict], cost_totals: dict,
    ) -> str:
        phases_count = len(plan.phases) if plan else 0
        tasks_count = plan.total_tasks if plan else 0
        cost_usd = cost_totals["total_cost_cents"] / 100

        md = [f"# Abschlussprotokoll: {title}\n"]
        md.append(f"**Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        md.append("## Übersicht\n")
        md.append(f"- **Phasen:** {phases_count}")
        md.append(f"- **Tasks:** {tasks_count}")
        md.append(f"- **Dateien geändert:** {len(files)}")
        md.append(f"- **Deviations:** {len(deviations)}")
        md.append(f"- **Oracle-Entscheidungen:** {len(decisions)}")
        md.append(f"- **API-Kosten:** ${cost_usd:.2f}")
        md.append(f"- **Tokens:** {cost_totals['total_input_tokens']:,} in / {cost_totals['total_output_tokens']:,} out\n")

        # Test instructions from spec acceptance criteria
        test_instructions = self._extract_test_instructions()
        if test_instructions:
            md.append("## Test-Anleitung\n")
            md.append("So kannst du die Änderungen testen:\n")
            for i, step in enumerate(test_instructions, 1):
                md.append(f"{i}. {step}")
            md.append("")

        # Manual testing hints based on file changes
        manual_steps = self._generate_manual_test_hints(files)
        if manual_steps:
            md.append("## Manuell zu prüfen\n")
            md.append("Diese Punkte sollten manuell verifiziert werden:\n")
            for step in manual_steps:
                md.append(f"- {step}")
            md.append("")

        if files:
            md.append("## Geänderte Dateien\n")
            for f in files[:30]:
                md.append(f"- `{f['path']}` (+{f['lines_added']}/-{f['lines_removed']})")
            if len(files) > 30:
                md.append(f"- ... und {len(files) - 30} weitere")
            md.append("")

        if decisions:
            md.append("## Oracle-Entscheidungen\n")
            for d in decisions[:15]:
                q = d['question'][:100] + "..." if len(d['question']) > 100 else d['question']
                md.append(f"**Q:** {q}\n**A:** {d['decision']}\n*{d['reason']}*\n")

        if deviations:
            md.append("## Deviations\n")
            for dev in deviations:
                md.append(f"- **{dev['type']}:** {dev['description']}")
            md.append("")

        if summaries:
            md.append("## Task-Details\n")
            for i, s in enumerate(summaries[:10], 1):
                lines = s.strip().split("\n")
                md.append(f"### {lines[0] if lines else f'Task {i}'}")
                match = re.search(r"## Was wurde gemacht\n(.+?)(?=\n##|\Z)", s, re.DOTALL)
                if match:
                    md.append(match.group(1).strip()[:300])
                md.append("")

        return "\n".join(md)

    def _extract_test_instructions(self) -> list[str]:
        """Extract test instructions from spec acceptance criteria."""
        spec_file = self.dirigent_dir / "SPEC.md"
        if not spec_file.exists():
            spec_file = self.repo_path / ".planning" / "SPEC.md"
        if not spec_file.exists():
            return []

        try:
            content = spec_file.read_text(encoding="utf-8")
            # Find acceptance criteria section
            ac_match = re.search(
                r"##\s*(?:Acceptance Criteria|Akzeptanzkriterien|AC)\s*\n(.*?)(?=\n##|\Z)",
                content, re.DOTALL | re.IGNORECASE
            )
            if not ac_match:
                return []

            ac_section = ac_match.group(1).strip()
            # Extract bullet points
            criteria = re.findall(r"[-*]\s*(.+?)(?=\n[-*]|\Z)", ac_section, re.DOTALL)
            # Convert to test steps
            test_steps = []
            for criterion in criteria[:8]:  # Max 8 steps
                step = criterion.strip().replace("\n", " ")
                # Make it actionable
                if not step.lower().startswith(("verify", "check", "test", "prüfe", "teste")):
                    step = f"Verifiziere: {step}"
                test_steps.append(step)
            return test_steps
        except Exception:
            return []

    def _generate_manual_test_hints(self, files: list[dict]) -> list[str]:
        """Generate manual testing hints based on changed files."""
        hints = []

        # Categorize files
        ui_files = [f for f in files if any(x in f["path"].lower() for x in
            ["component", "page", "view", ".tsx", ".jsx", ".vue", ".svelte", "template"])]
        api_files = [f for f in files if any(x in f["path"].lower() for x in
            ["api/", "route", "endpoint", "controller", "handler"])]
        test_files = [f for f in files if any(x in f["path"].lower() for x in
            ["test", "spec", ".test.", ".spec."])]
        migration_files = [f for f in files if any(x in f["path"].lower() for x in
            ["migration", "schema", ".sql"])]
        config_files = [f for f in files if any(x in f["path"].lower() for x in
            ["config", ".env", "settings", "package.json", "requirements"])]

        if ui_files:
            hints.append(f"UI-Änderungen in {len(ui_files)} Dateien - Browser öffnen und visuell prüfen")

        if api_files:
            hints.append(f"API-Änderungen in {len(api_files)} Dateien - API-Endpunkte mit Postman/curl testen")

        if not test_files and (ui_files or api_files):
            hints.append("Keine Tests hinzugefügt - manuelle Tests empfohlen")

        if migration_files:
            hints.append("Datenbank-Migrationen geändert - auf staging deployen und prüfen")

        if config_files:
            hints.append("Konfigurationsdateien geändert - Umgebungsvariablen prüfen")

        # Check for new dependencies
        for f in files:
            if "package.json" in f["path"] and f["lines_added"] > 0:
                hints.append("`npm install` ausführen (neue Dependencies)")
                break
            if "requirements" in f["path"] and f["lines_added"] > 0:
                hints.append("`pip install -r requirements.txt` ausführen (neue Dependencies)")
                break

        return hints[:6]  # Max 6 hints

    def _collect_token_usage(self) -> dict:
        """Read token usage directly from Claude Code transcript files.

        Claude Code stores session transcripts in ~/.claude/projects/<project-key>/*.jsonl
        Each assistant message contains usage data that we sum up.

        Only counts transcripts created after the execution started (from state.started_at)
        to avoid counting tokens from previous executions on the same workspace.

        Returns dict with:
            - input_tokens: total input (including cache)
            - output_tokens: total output
            - cache_creation_tokens: tokens written to cache
            - cache_read_tokens: tokens read from cache (discounted)
            - cost_cents: calculated cost in cents based on model pricing
            - usage_by_model: breakdown by model
        """
        total_input = 0
        total_output = 0
        total_cache_creation = 0
        total_cache_read = 0
        total_cost_cents = 0.0
        files_processed = 0
        files_skipped = 0
        usage_by_model: dict[str, dict] = {}  # model -> {input, output, cache_read, cache_write, cost}

        # Get execution start time from state
        state = load_state(str(self.repo_path))
        started_at_str = state.get("started_at") if state else None
        started_at_ts = None
        if started_at_str:
            try:
                started_at_ts = datetime.fromisoformat(started_at_str).timestamp()
            except (ValueError, TypeError):
                pass

        # Find Claude projects directory
        claude_projects_dir = Path.home() / ".claude" / "projects"
        if not claude_projects_dir.exists():
            logger.warning(f"Claude projects directory not found: {claude_projects_dir}")
            return {"input_tokens": 0, "output_tokens": 0, "cache_creation_tokens": 0, "cache_read_tokens": 0, "cost_cents": 0, "usage_by_model": {}}

        # Build project key pattern from repo path (Claude uses path with dashes)
        # e.g., /home/coder/outbit-portal -> -home-coder-outbit-portal
        repo_path_str = str(self.repo_path.resolve())
        project_key = repo_path_str.replace("/", "-")
        if not project_key.startswith("-"):
            project_key = "-" + project_key

        # Find matching project directories
        matching_dirs = []
        for d in claude_projects_dir.iterdir():
            if d.is_dir() and project_key in d.name:
                matching_dirs.append(d)

        if not matching_dirs:
            # Try without leading dash
            project_key_alt = project_key.lstrip("-")
            for d in claude_projects_dir.iterdir():
                if d.is_dir() and project_key_alt in d.name:
                    matching_dirs.append(d)

        if not matching_dirs:
            logger.warning(f"No Claude project directory found matching: {project_key}")
            logger.debug(f"Available directories: {[d.name for d in claude_projects_dir.iterdir() if d.is_dir()]}")
            return {"input_tokens": 0, "output_tokens": 0, "cache_creation_tokens": 0, "cache_read_tokens": 0, "cost_cents": 0, "usage_by_model": {}}

        logger.info(f"Found {len(matching_dirs)} Claude project directories matching repo")

        # Read JSONL transcript files (only entries created after execution started)
        for project_dir in matching_dirs:
            for transcript_file in project_dir.glob("*.jsonl"):
                try:
                    # Skip files that haven't been modified since execution started
                    # (optimization to avoid reading old files entirely)
                    if started_at_ts:
                        file_mtime = transcript_file.stat().st_mtime
                        if file_mtime < started_at_ts:
                            files_skipped += 1
                            continue

                    with open(transcript_file, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)

                                # Filter by entry timestamp (not just file mtime)
                                # Each entry has a 'timestamp' field like "2025-03-27T13:11:52.636Z"
                                if started_at_ts and "timestamp" in entry:
                                    try:
                                        entry_ts_str = entry["timestamp"]
                                        # Parse ISO timestamp (handle both with and without Z suffix)
                                        if entry_ts_str.endswith("Z"):
                                            entry_ts_str = entry_ts_str[:-1] + "+00:00"
                                        entry_ts = datetime.fromisoformat(entry_ts_str).timestamp()
                                        if entry_ts < started_at_ts:
                                            continue  # Skip entries from before this execution
                                    except (ValueError, TypeError):
                                        pass  # If we can't parse, include the entry

                                # Look for assistant messages with usage data
                                if entry.get("type") == "assistant" and "message" in entry:
                                    message = entry["message"]
                                    usage = message.get("usage", {})
                                    model = message.get("model", "unknown")

                                    if usage:
                                        input_tokens = usage.get("input_tokens", 0)
                                        output_tokens = usage.get("output_tokens", 0)
                                        cache_creation = usage.get("cache_creation_input_tokens", 0)
                                        cache_read = usage.get("cache_read_input_tokens", 0)

                                        # Accumulate totals
                                        total_input += input_tokens
                                        total_output += output_tokens
                                        total_cache_creation += cache_creation
                                        total_cache_read += cache_read

                                        # Calculate cost for this message
                                        input_price, output_price = _get_model_pricing(model)

                                        # Cost calculation:
                                        # - Regular input: full price
                                        # - Cache writes: 1.25x input price
                                        # - Cache reads: 0.1x input price
                                        # - Output: full output price
                                        input_cost = (input_tokens / 1_000_000) * input_price
                                        cache_write_cost = (cache_creation / 1_000_000) * input_price * 1.25
                                        cache_read_cost = (cache_read / 1_000_000) * input_price * 0.1
                                        output_cost = (output_tokens / 1_000_000) * output_price

                                        message_cost = input_cost + cache_write_cost + cache_read_cost + output_cost
                                        total_cost_cents += message_cost * 100  # Convert to cents

                                        # Track by model
                                        if model not in usage_by_model:
                                            usage_by_model[model] = {
                                                "input_tokens": 0,
                                                "output_tokens": 0,
                                                "cache_read_tokens": 0,
                                                "cache_write_tokens": 0,
                                                "cost_cents": 0.0,
                                            }
                                        usage_by_model[model]["input_tokens"] += input_tokens
                                        usage_by_model[model]["output_tokens"] += output_tokens
                                        usage_by_model[model]["cache_read_tokens"] += cache_read
                                        usage_by_model[model]["cache_write_tokens"] += cache_creation
                                        usage_by_model[model]["cost_cents"] += message_cost * 100
                            except json.JSONDecodeError:
                                continue
                    files_processed += 1
                except Exception as e:
                    logger.debug(f"Error reading transcript {transcript_file}: {e}")
                    continue

        total_in = total_input + total_cache_creation + total_cache_read
        cost_usd = total_cost_cents / 100

        logger.info(f"Collected token usage from {files_processed} transcript files "
                   f"(skipped {files_skipped} older files): "
                   f"{total_in:,} input (raw: {total_input:,}, cache_create: {total_cache_creation:,}, cache_read: {total_cache_read:,}), "
                   f"{total_output:,} output, ${cost_usd:.4f} estimated cost")

        # Log breakdown by model if multiple models used
        if len(usage_by_model) > 1:
            for model, stats in sorted(usage_by_model.items(), key=lambda x: -x[1]["cost_cents"]):
                logger.debug(f"  {model}: {stats['input_tokens']:,} in, {stats['output_tokens']:,} out, "
                           f"${stats['cost_cents']/100:.4f}")

        return {
            "input_tokens": total_input + total_cache_creation + total_cache_read,
            "output_tokens": total_output,
            "cache_creation_tokens": total_cache_creation,
            "cache_read_tokens": total_cache_read,
            "cost_cents": int(round(total_cost_cents)),
            "usage_by_model": usage_by_model,
        }

    def _send_summary_to_portal(
        self, markdown: str, files_changed: list[dict],
        decisions: list[dict], deviations: list[dict],
        branch_name: Optional[str], pr_url: Optional[str],
        test_instructions: list[str] = None, manual_hints: list[str] = None,
    ):
        # Use direct credentials from Executor, fallback to questioner
        portal_url = self.portal_url
        execution_id = self.execution_id
        reporter_token = self.reporter_token

        if not portal_url or not execution_id:
            # Try questioner as fallback
            from outbid_dirigent.dirigent import get_questioner
            questioner = get_questioner()
            if questioner and hasattr(questioner, 'portal_url'):
                portal_url = questioner.portal_url
                execution_id = questioner.execution_id
                reporter_token = questioner.reporter_token

        if not portal_url or not execution_id or not reporter_token:
            logger.debug("No portal credentials available, skipping summary upload")
            return

        # Collect token usage directly from Claude Code transcripts
        token_usage = self._collect_token_usage()
        cost_cents = token_usage.get("cost_cents", 0)
        logger.info(f"Token usage collected: {token_usage['input_tokens']:,} input, "
                   f"{token_usage['output_tokens']:,} output, ${cost_cents/100:.4f} cost")

        # Calculate duration
        elapsed_ms = 0
        if self._legacy_logger and hasattr(self._legacy_logger, '_start_time') and self._legacy_logger._start_time:
            elapsed = datetime.now() - self._legacy_logger._start_time
            elapsed_ms = int(elapsed.total_seconds() * 1000)

        # Build summary payload
        summary_data = {
            "markdown": markdown,
            "filesChanged": files_changed,
            "decisions": [
                {"question": d["question"][:200], "decision": d["decision"], "reason": d["reason"]}
                for d in decisions
            ] if decisions else [],
            "deviations": deviations or [],
            "branchName": branch_name,
            "prUrl": pr_url,
            "totalCommits": self._legacy_logger._total_commits if self._legacy_logger and hasattr(self._legacy_logger, '_total_commits') else 0,
            "durationMs": elapsed_ms,
            "testInstructions": test_instructions or [],
            "manualHints": manual_hints or [],
            # Token usage from Claude Code sessions
            "totalInputTokens": token_usage["input_tokens"],
            "totalOutputTokens": token_usage["output_tokens"],
            "totalCostCents": token_usage.get("cost_cents", 0),
        }

        try:
            logger.info(f"Sending summary to portal: {portal_url}/api/execution-event")
            response = requests.post(
                f"{portal_url}/api/execution-event",
                headers={
                    "Content-Type": "application/json",
                    "X-Reporter-Token": reporter_token,
                },
                json={
                    "execution_id": execution_id,
                    "event": {
                        "type": "summary",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "data": summary_data,
                    }
                },
                timeout=30,
            )
            if response.ok:
                logger.info(f"Summary sent successfully: {len(files_changed)} files, "
                          f"{token_usage['input_tokens']:,} input tokens, ${cost_cents/100:.4f}")
            else:
                logger.warning(f"Summary upload failed: {response.status_code} - {response.text[:200]}")
        except requests.RequestException as e:
            logger.error(f"Summary upload failed: {e}")

    # ══════════════════════════════════════════
    # PREVIEW SCRIPT GENERATION
    # ══════════════════════════════════════════

    def generate_preview_script(self) -> bool:
        """Generate ~/preview-start.sh for workspace preview."""
        logger.info("Generating preview script...")
        return self._generate_preview_from_runtime()

    def _generate_preview_from_runtime(self) -> bool:
        """Fallback: generate preview script from RuntimeAnalysis."""
        analysis = load_analysis(str(self.repo_path))
        if not analysis or "runtime" not in analysis:
            logger.warning("No manifest or runtime analysis found, skipping preview script")
            return False

        runtime = analysis["runtime"]
        project_name = analysis.get("repo_name", "project")
        services = runtime.get("services", [])
        start_command = runtime.get("start_command", "npm run dev")
        uses_doppler = runtime.get("uses_doppler", False)

        script_lines = [
            "#!/bin/bash",
            "# Preview Start Script - Generated by Outbid Dirigent (from runtime analysis)",
            "",
            "set -e",
            "",
            'DOPPLER_TOKEN="${1:-$DOPPLER_TOKEN}"',
            "",
        ]

        if services:
            script_lines.append("# ─── Start Required Services ───")
            script_lines.append("")
            for service in services:
                name = service.get("name", "service")
                docker_image = service.get("docker_image")
                port = service.get("port")
                env_vars = service.get("env_vars", [])
                if docker_image:
                    container_name = name.lower().replace(" ", "_")
                    script_lines.append(f"# {name}")
                    script_lines.append(f'if ! docker ps --format "{{{{.Names}}}}" | grep -q "^{container_name}$"; then')
                    docker_cmd = f"  docker run -d --name {container_name}"
                    for env_var in env_vars:
                        docker_cmd += f' -e "{env_var}"'
                    if port:
                        docker_cmd += f" -p {port}:{port}"
                    docker_cmd += f" {docker_image}"
                    script_lines.append(docker_cmd)
                    script_lines.append("else")
                    script_lines.append(f'  echo "{name} already running"')
                    script_lines.append("fi")
                    script_lines.append("")
            script_lines.append("sleep 3")
            script_lines.append("")

        script_lines.append(f"cd ~/{project_name}")
        script_lines.append("")

        setup_steps = runtime.get("setup_steps", [])
        if setup_steps:
            script_lines.append('if [ ! -f ".setup_done" ]; then')
            for step in setup_steps:
                script_lines.append(f"  {step}")
            script_lines.append('  touch ".setup_done"')
            script_lines.append("fi")
            script_lines.append("")

        if uses_doppler:
            script_lines.append('if [ -n "$DOPPLER_TOKEN" ]; then')
            script_lines.append(f'  exec doppler run --token "$DOPPLER_TOKEN" -- {start_command}')
            script_lines.append("else")
            script_lines.append(f"  exec {start_command}")
            script_lines.append("fi")
        else:
            script_lines.append('if [ -n "$DOPPLER_TOKEN" ]; then')
            script_lines.append(f'  exec doppler run --token "$DOPPLER_TOKEN" -- {start_command}')
            script_lines.append("else")
            script_lines.append(f"  exec {start_command}")
            script_lines.append("fi")

        return self._write_preview_script(
            script_lines, runtime.get("port", 3000), runtime.get("framework"),
            start_command, [s.get("name") for s in services],
            uses_doppler, runtime.get("health_check_path"),
        )

    def _write_preview_script(
        self, script_lines: list[str], port: int, framework: str | None,
        start_command: str, service_names: list[str],
        uses_doppler: bool, health_check: str | None,
    ) -> bool:
        """Write the preview script and metadata."""
        script_content = "\n".join(script_lines) + "\n"
        home_dir = Path.home()
        script_path = home_dir / "preview-start.sh"

        try:
            script_path.write_text(script_content, encoding="utf-8")
            script_path.chmod(0o755)
            logger.info(f"Preview script written to {script_path}")
        except Exception as e:
            logger.error(f"Failed to write preview script: {e}")
            return False

        metadata = {
            "port": port,
            "framework": framework,
            "start_command": start_command,
            "services": service_names,
            "uses_doppler": uses_doppler,
            "health_check": health_check,
            "generated_at": datetime.now().isoformat(),
        }

        metadata_path = self.dirigent_dir / "PREVIEW_META.json"
        try:
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Preview metadata written to {metadata_path}")
        except Exception as e:
            logger.warning(f"Failed to write preview metadata: {e}")

        return True


def create_executor(
    repo_path: str, spec_path: str,
    dry_run: bool = False, use_proteus: bool = False,
    model: str = "", effort: str = "",
    portal_url: str = "", execution_id: str = "", reporter_token: str = "",
) -> Executor:
    """Factory function for Executor."""
    return Executor(
        repo_path, spec_path, dry_run, use_proteus, model, effort,
        portal_url, execution_id, reporter_token,
    )
