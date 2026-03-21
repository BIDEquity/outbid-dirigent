"""
Planner — creates execution plans via Claude Code.

Extracted from the Executor god class. Handles:
- Building the plan creation prompt
- Running Claude Code to generate PLAN.json
- Loading and validating the result
"""

from pathlib import Path
from typing import Optional

from loguru import logger

from outbid_dirigent.plan_schema import Plan
from outbid_dirigent.task_runner import TaskRunner
from outbid_dirigent.test_manifest import TestManifest


class Planner:
    """Creates PLAN.json via Claude Code."""

    def __init__(self, repo_path: Path, spec_content: str, runner: TaskRunner):
        self.repo_path = repo_path
        self.spec_content = spec_content
        self.runner = runner
        self.dirigent_dir = repo_path / ".dirigent"

    def create_plan(self) -> Optional[Plan]:
        """Generate PLAN.json via Claude Code. Returns Plan or None on failure."""
        business_rules = self.runner._load_business_rules()
        br_context = ""
        if business_rules:
            br_context = f"""
## Business Rules (müssen erhalten bleiben!)
{business_rules[:3000]}
{"... (truncated)" if len(business_rules) > 3000 else ""}
"""

        context_file = self.dirigent_dir / "CONTEXT.md"
        repo_context = ""
        if context_file.exists():
            repo_context = f"\n## Repo-Kontext\n{context_file.read_text(encoding='utf-8')}\n"

        # Test manifest context
        manifest = TestManifest.load(self.repo_path)
        manifest_context = ""
        if manifest:
            l1_cmds = ", ".join(f"`{c.run}`" for c in manifest.commands_for_level("l1"))
            l2_cmds = ", ".join(f"`{c.run}`" for c in manifest.commands_for_level("l2"))
            real_comps = [c for c in manifest.components if not c.is_mocked]
            comp_names = ", ".join(c.name for c in real_comps)
            mocked = manifest.mocked_components()
            mocked_names = ", ".join(c.name for c in mocked) if mocked else "keine"
            gaps = ", ".join(manifest.gap_strings()) if manifest.gaps else "keine"

            manifest_context = f"""
## Test-Manifest vorhanden
Nutze es fuer Task-Planung:
- L1 verfuegbar: {l1_cmds or 'keine'}
- L2 verfuegbar: {l2_cmds or 'keine'} (braucht: {comp_names or 'nichts'})
- Auto-mocked (kein Setup): {mocked_names}
- Bekannte Gaps: {gaps}
- Tasks die testen sollen: test_level auf "L1" oder "L2" setzen
- Tasks die NICHT testen koennen (Gap): test_level leer lassen
- Keine eigenen Test-Befehle erfinden — nur Manifest-Commands verwenden
- Am Ende laeuft ein zentraler TEST-Schritt ueber alle Aenderungen
"""

        prompt = f"""Erstelle einen Ausführungsplan für dieses Feature.

# Spec
{self.spec_content}

{br_context}
{repo_context}
{manifest_context}

Erstelle die Datei .dirigent/PLAN.json mit diesem Format:
{Plan.json_template()}

Regeln:
- Maximal 4 Phasen
- Maximal 4 Tasks pro Phase
- Jeder Task ist atomar (macht genau eine Sache)
- Keine Abhängigkeiten zwischen Tasks innerhalb einer Phase
- Tasks müssen konkret und ausführbar sein
- Bei Legacy-Migration: Alle Business Rules müssen erhalten bleiben
- Für "model": Verwende "haiku" für einfache Tasks (delete files, add imports, kleine Änderungen), "sonnet" für Standard-Tasks (neue Methoden, Tests, Refactoring), "opus" nur für sehr komplexe Architektur-Tasks
- Für "effort": "low" für mechanische Tasks, "medium" für Standard, "high" für komplexe Logik
- Für "test_level": "L1" wenn der Task mit Unit Tests/Lint verifiziert werden soll, "L2" wenn Integration Tests nötig sind, leer wenn kein Testing nötig
- Für "assumptions": Liste alle Annahmen über die Codebase auf (z.B. "Tests laufen mit pytest")
- Für "out_of_scope": Liste explizit auf was NICHT gemacht werden soll

Erstelle den Plan jetzt.
"""

        success, _, stderr = self.runner._run_claude(prompt, timeout=1800)
        if not success:
            logger.error(f"Plan creation failed: {stderr}")
            return None

        plan_file = self.dirigent_dir / "PLAN.json"
        plan = Plan.load(plan_file)
        if plan is None:
            logger.error("PLAN.json was not created or is invalid")
            return None

        logger.info(f"Plan: {len(plan.phases)} phases, {plan.total_tasks} tasks")
        if plan.assumptions:
            logger.info(f"Assumptions: {len(plan.assumptions)}")
        if plan.out_of_scope:
            logger.info(f"Out of scope: {len(plan.out_of_scope)}")

        return plan
