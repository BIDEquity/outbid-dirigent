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
from outbid_dirigent.oracle import Oracle, create_oracle
from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.planner import Planner
from outbid_dirigent.proteus_integration import ProteusIntegration, create_proteus_integration
from outbid_dirigent.router import load_state, save_state, mark_step_complete
from outbid_dirigent.shipper import Shipper
from outbid_dirigent.task_runner import TaskRunner, TaskResult


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
    ):
        self.repo_path = Path(repo_path).resolve()
        self.spec_path = Path(spec_path).resolve()
        self.use_proteus = use_proteus
        self.dry_run = dry_run
        self.oracle = create_oracle(str(self.repo_path))

        # Directories
        self.dirigent_dir = self.repo_path / ".dirigent"
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

        # Spec content
        self.spec_content = self.spec_path.read_text(encoding="utf-8")

        # Compose modules
        self.runner = TaskRunner(
            repo_path=self.repo_path,
            spec_content=self.spec_content,
            default_model=model,
            default_effort=effort,
        )
        self.planner = Planner(
            repo_path=self.repo_path,
            spec_content=self.spec_content,
            runner=self.runner,
        )

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
    # TEST MANIFEST GENERATION
    # ══════════════════════════════════════════

    def generate_test_manifest(self) -> bool:
        """Generate outbid-test-manifest.yaml via 3x sonnet + haiku consolidation."""
        from outbid_dirigent.test_manifest import TestManifest, ManifestGenerator

        # Skip if manifest already exists
        manifest_path = self.repo_path / "outbid-test-manifest.yaml"
        if manifest_path.exists():
            logger.info(f"Test manifest already exists: {manifest_path}")
            return True

        generator = ManifestGenerator(self.repo_path, self.runner)
        manifest = generator.generate()
        return manifest is not None

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

        prompt = f"""Analysiere diese {language} Codebase und extrahiere alle Business Rules.

Erstelle die Datei .dirigent/BUSINESS_RULES.md mit folgendem Format:

# Business Rules – {self.repo_path.name}

## Kern-Entitäten
(Alle Domain-Objekte und ihre Felder)

## Geschäftsregeln
(Validierungen, Berechnungen, Constraints)

## Domain Events
(Was passiert wann? User erstellt X → Y wird ausgelöst)

## API Endpoints
(Alle Routes mit Parametern und Response-Format)

## Datenbank
(Schema, Relationen, Constraints)

## Externe Abhängigkeiten
(APIs, Services, Integrations)

## Edge Cases
(Bekannte Sonderfälle und wie sie behandelt werden)

Regeln:
- Sei präzise. Keine Annahmen. Nur was du im Code siehst.
- Dokumentiere numerische Werte exakt (Limits, Timeouts, etc.)
- Bei Unsicherheit, markiere es mit [UNKLAR]
- Analysiere alle relevanten Dateien systematisch

Erstelle die Datei jetzt.
"""

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
        prompt = f"""Analysiere diese Codebase um das folgende Feature zu implementieren:

{self.spec_content}

Identifiziere die relevanten Dateien und erstelle .dirigent/CONTEXT.md mit:

# Relevante Dateien für Feature

## Hauptdateien
(Die Dateien die direkt modifiziert werden müssen)

## Abhängigkeiten
(Dateien die verstanden werden müssen aber nicht geändert werden)

## Patterns
(Coding-Patterns die im Projekt verwendet werden)

## Integration Points
(Wo das neue Feature sich einfügen muss)

Fokussiere dich NUR auf die für dieses Feature relevanten Teile.
Keine vollständige Codebase-Analyse nötig.
"""
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
            phase_details = [
                {"phase": p.id, "name": p.name, "taskCount": len(p.tasks)}
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
                    self._legacy_logger.task_start(task.id, task.name, phase=phase.id)

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
                            self._legacy_logger.deviation(dev["type"], dev["description"], task_id=task.id, phase=phase.id)
                        self._legacy_logger.task_done(task.id, result.commit_hash, task_name=task.name, phase=phase.id)
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

            # Phase review — code review + fix cycle
            self._review_phase(phase, plan)

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
    # PHASE REVIEW (code review + fix)
    # ══════════════════════════════════════════

    def _review_phase(self, phase, plan: Plan):
        """Launch a Claude process that runs code-review then fix on the phase's changes."""
        # Collect what this phase changed
        commit_count = len(phase.tasks)
        if commit_count == 0:
            return

        logger.info(f"Phase {phase.id} review: reviewing {commit_count} task commits")

        # Build the diff of this phase's work
        diff_cmd = f"git diff HEAD~{commit_count} --stat"

        # File list for context
        files_modified = []
        files_created = []
        for task in phase.tasks:
            files_modified.extend(task.files_to_modify)
            files_created.extend(task.files_to_create)
        all_files = sorted(set(files_modified + files_created))

        prompt = f"""Du bist ein Post-Phase Reviewer. Phase {phase.id} ("{phase.name}") wurde gerade abgeschlossen.

# Deine Aufgabe
Fuehre zwei Schritte sequentiell aus:

## Schritt 1: Code Review (Agent)
Starte einen Agent mit folgendem Auftrag:
- Pruefe den Diff der letzten {commit_count} Commits: `{diff_cmd}`
- Lies die geaenderten Dateien und pruefe auf:
  1. **Bugs**: None-Checks, fehlende Parameter-Validierung, falsche Typen
  2. **API-Kompatibilitaet**: Werden bestehende Funktionssignaturen gebrochen? Werden Parameter die None sein koennen ohne Guard verwendet?
  3. **Unvollstaendige Arbeit**: TODOs, auskommentierter Code, fehlende Imports
  4. **Logik-Fehler**: Off-by-one, falsche Vergleiche, fehlende Edge Cases
- Schreibe die Findings in .dirigent/reviews/phase-{phase.id}-REVIEW.md
- Format: Severity (CRITICAL/WARN/INFO), Datei:Zeile, Beschreibung, Fix-Vorschlag

Dateien die in dieser Phase geaendert wurden:
{chr(10).join(f'- {f}' for f in all_files) if all_files else '(siehe git diff)'}

## Schritt 2: Fix (Agent)
Starte einen zweiten Agent der:
- .dirigent/reviews/phase-{phase.id}-REVIEW.md liest
- Alle CRITICAL und WARN Findings fixt
- git add -A && git commit -m "fix(phase-{phase.id}): post-review fixes"
- Wenn keine Findings: nichts tun

Wichtig:
- Schritt 2 erst starten NACHDEM Schritt 1 fertig ist
- Keine neuen Features einfuehren, nur Bugs fixen
- Wenn der Review keine CRITICAL/WARN Findings hat, ueberspringe Schritt 2
"""

        sys_prompt = f"""Du orchestrierst zwei Agents sequentiell: erst Review, dann Fix.
Nutze den Agent-Tool fuer beide Schritte. Warte auf das Ergebnis von Schritt 1 bevor du Schritt 2 startest.
Keine eigenen Code-Aenderungen — nur ueber die Agents arbeiten."""

        success, stdout, stderr = self.runner._run_claude(
            prompt, timeout=600, system_prompt=sys_prompt,
        )

        if success:
            review_file = self.dirigent_dir / "reviews" / f"phase-{phase.id}-REVIEW.md"
            if review_file.exists():
                content = review_file.read_text(encoding="utf-8")
                critical_count = content.lower().count("critical")
                warn_count = content.lower().count("warn")
                logger.info(f"Phase {phase.id} review: {critical_count} critical, {warn_count} warnings")
            else:
                logger.info(f"Phase {phase.id} review: no review file created")
        else:
            logger.warning(f"Phase {phase.id} review failed (non-blocking): {stderr[:200]}")

    # ══════════════════════════════════════════
    # TEST STEP
    # ══════════════════════════════════════════

    def run_tests(self) -> bool:
        """Run full test suite from test manifest. Returns True if passed or no manifest."""
        from outbid_dirigent.test_manifest import TestManifest, TestStepRunner

        manifest = TestManifest.load(self.repo_path)
        if not manifest:
            logger.info("No test manifest found, skipping test step")
            return True

        logger.info("Running test suite from manifest...")
        runner = TestStepRunner(self.repo_path, manifest)
        result = runner.run()

        if result.summary:
            logger.info(f"Test results:\n{result.summary}")

        if result.skipped_levels:
            logger.warning(f"Skipped test levels: {', '.join(result.skipped_levels)}")

        if result.passed:
            logger.info("All tests passed")
        else:
            logger.error("Tests failed — blocking ship")

        return result.passed

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

        markdown = self._generate_summary_markdown(
            plan_title, plan, summaries, decisions, files_changed, deviations, cost_totals
        )

        if self._legacy_logger:
            self._legacy_logger.summary(
                markdown=markdown,
                files_changed=files_changed,
                decisions=[{"question": d["question"][:200], "decision": d["decision"], "reason": d["reason"]} for d in decisions],
                deviations=deviations,
                total_cost_cents=cost_totals["total_cost_cents"],
                total_input_tokens=cost_totals["total_input_tokens"],
                total_output_tokens=cost_totals["total_output_tokens"],
            )

        self._send_summary_to_portal(markdown, files_changed, decisions, deviations, branch_name, pr_url)

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
        try:
            result = subprocess.run(
                ["git", "diff", "--numstat", "HEAD~20..HEAD"],
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
        except Exception:
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

    def _send_summary_to_portal(
        self, markdown: str, files_changed: list[dict],
        decisions: list[dict], deviations: list[dict],
        branch_name: Optional[str], pr_url: Optional[str],
    ):
        from outbid_dirigent.dirigent import get_questioner
        questioner = get_questioner()
        if not questioner or not hasattr(questioner, 'portal_url'):
            return

        try:
            elapsed = datetime.now() - (self._legacy_logger._start_time if self._legacy_logger else datetime.now())
            requests.post(
                f"{questioner.portal_url}/api/execution-event",
                headers={"X-Reporter-Token": questioner.reporter_token},
                json={
                    "execution_id": questioner.execution_id,
                    "event": {
                        "type": "summary",
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "data": {
                            "markdown": markdown,
                            "filesChanged": files_changed,
                            "decisions": [{"question": d["question"][:200], "decision": d["decision"], "reason": d["reason"]} for d in decisions],
                            "deviations": deviations,
                            "branchName": branch_name,
                            "prUrl": pr_url,
                            "totalCommits": self._legacy_logger._total_commits if self._legacy_logger else 0,
                            "durationMs": int(elapsed.total_seconds() * 1000),
                        }
                    }
                },
                timeout=30,
            )
        except requests.RequestException as e:
            logger.debug(f"Summary upload failed: {e}")

    # ══════════════════════════════════════════
    # PREVIEW SCRIPT GENERATION
    # ══════════════════════════════════════════

    def generate_preview_script(self) -> bool:
        """Generate ~/preview-start.sh for workspace preview.

        This script is used by the Portal to start a preview of the built app.
        It's based on the runtime analysis performed before building.
        """
        logger.info("Generating preview script...")

        # Load runtime analysis
        analysis = load_analysis(str(self.repo_path))
        if not analysis or "runtime" not in analysis:
            logger.warning("No runtime analysis found, skipping preview script generation")
            return False

        runtime = analysis["runtime"]
        project_name = analysis.get("repo_name", "project")

        # Build the script
        script_lines = [
            "#!/bin/bash",
            "# Preview Start Script - Generated by Outbid Dirigent",
            "# This script starts all necessary services and the dev server",
            "",
            "set -e",
            "",
            "# Accept Doppler token as argument or from environment",
            'DOPPLER_TOKEN="${1:-$DOPPLER_TOKEN}"',
            "",
        ]

        # Add service startup commands
        services = runtime.get("services", [])
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

                    # Check if container already running
                    script_lines.append(f"# {name}")
                    script_lines.append(f'if ! docker ps --format "{{{{.Names}}}}" | grep -q "^{container_name}$"; then')
                    script_lines.append(f'  echo "Starting {name}..."')

                    # Build docker run command
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

            # Wait for services to be ready
            script_lines.append("# Wait for services to be ready")

            for service in services:
                if service.get("type") == "database" and service.get("name") == "PostgreSQL":
                    script_lines.append('echo "Waiting for PostgreSQL..."')
                    script_lines.append("until docker exec postgres pg_isready -q 2>/dev/null; do sleep 1; done")
                elif service.get("type") == "database" and service.get("name") == "MySQL":
                    script_lines.append('echo "Waiting for MySQL..."')
                    script_lines.append('until docker exec mysql mysqladmin ping -h localhost --silent 2>/dev/null; do sleep 1; done')
                elif service.get("type") == "cache" and service.get("name") == "Redis":
                    script_lines.append('echo "Waiting for Redis..."')
                    script_lines.append("until docker exec redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 1; done")

            script_lines.append('echo "All services ready!"')
            script_lines.append("")

        # Change to project directory
        script_lines.append("# ─── Setup Project ───")
        script_lines.append("")
        script_lines.append(f"cd ~/{project_name}")
        script_lines.append("")

        # Setup steps (if not already done)
        setup_steps = runtime.get("setup_steps", [])
        if setup_steps:
            script_lines.append("# Run setup if needed")
            script_lines.append('if [ ! -f ".setup_done" ]; then')
            for step in setup_steps:
                script_lines.append(f'  echo "Running: {step}"')
                script_lines.append(f"  {step}")
            script_lines.append('  touch ".setup_done"')
            script_lines.append("fi")
            script_lines.append("")

        # Start the dev server
        script_lines.append("# ─── Start Dev Server ───")
        script_lines.append("")

        start_command = runtime.get("start_command", "npm run dev")
        uses_doppler = runtime.get("uses_doppler", False)

        if uses_doppler:
            script_lines.append('if [ -n "$DOPPLER_TOKEN" ]; then')
            script_lines.append('  echo "Starting with Doppler secrets..."')
            script_lines.append(f'  exec doppler run --token "$DOPPLER_TOKEN" -- {start_command}')
            script_lines.append("else")
            script_lines.append('  echo "Warning: No Doppler token provided, starting without secrets"')
            script_lines.append(f"  exec {start_command}")
            script_lines.append("fi")
        else:
            # Even without Doppler config, support token if provided
            script_lines.append('if [ -n "$DOPPLER_TOKEN" ]; then')
            script_lines.append('  echo "Starting with Doppler secrets..."')
            script_lines.append(f'  exec doppler run --token "$DOPPLER_TOKEN" -- {start_command}')
            script_lines.append("else")
            script_lines.append(f"  exec {start_command}")
            script_lines.append("fi")

        # Write the script
        script_content = "\n".join(script_lines) + "\n"
        home_dir = Path.home()
        script_path = home_dir / "preview-start.sh"

        try:
            script_path.write_text(script_content, encoding="utf-8")
            script_path.chmod(0o755)  # Make executable
            logger.info(f"Preview script written to {script_path}")
        except Exception as e:
            logger.error(f"Failed to write preview script: {e}")
            return False

        # Write metadata for the Portal
        metadata = {
            "port": runtime.get("port", 3000),
            "framework": runtime.get("framework"),
            "start_command": start_command,
            "services": [s.get("name") for s in services],
            "uses_doppler": uses_doppler,
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
) -> Executor:
    """Factory function for Executor."""
    return Executor(repo_path, spec_path, dry_run, use_proteus, model, effort)
