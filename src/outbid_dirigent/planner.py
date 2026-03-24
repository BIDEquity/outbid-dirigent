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
            truncated = business_rules[:3000]
            suffix = "\n... (truncated)" if len(business_rules) > 3000 else ""
            br_context = f"<business-rules hint=\"muessen erhalten bleiben\">\n{truncated}{suffix}\n</business-rules>"

        context_file = self.dirigent_dir / "CONTEXT.md"
        repo_context = ""
        if context_file.exists():
            repo_context = f"<repo-context>\n{context_file.read_text(encoding='utf-8')}\n</repo-context>"

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

            manifest_context = f"""<test-manifest>
<level name="L1">{l1_cmds or 'keine'}</level>
<level name="L2" requires="{comp_names or 'nichts'}">{l2_cmds or 'keine'}</level>
<auto-mocked>{mocked_names}</auto-mocked>
<gaps>{gaps}</gaps>
<planning-rules>
<rule>Tasks die testen sollen: test_level auf "L1" oder "L2" setzen</rule>
<rule>Tasks die NICHT testen koennen (Gap): test_level leer lassen</rule>
<rule>Keine eigenen Test-Befehle erfinden — nur Manifest-Commands verwenden</rule>
<rule>Am Ende laeuft ein zentraler TEST-Schritt ueber alle Aenderungen</rule>
</planning-rules>
</test-manifest>"""

        prompt = f"""<task>Erstelle einen Ausfuehrungsplan fuer dieses Feature.</task>

<spec>
{self.spec_content}
</spec>

{br_context}
{repo_context}
{manifest_context}

<output-format>
Erstelle die Datei .dirigent/PLAN.json mit diesem Format:
{Plan.json_template()}
</output-format>

<rules>
<rule>Maximal 4 Phasen</rule>
<rule>Maximal 4 Tasks pro Phase</rule>
<rule>Jeder Task ist atomar (macht genau eine Sache)</rule>
<rule>Keine Abhaengigkeiten zwischen Tasks innerhalb einer Phase</rule>
<rule>Tasks muessen konkret und ausfuehrbar sein</rule>
<rule>Bei Legacy-Migration: Alle Business Rules muessen erhalten bleiben</rule>
<rule name="model">Verwende "haiku" fuer einfache Tasks (delete files, add imports, kleine Aenderungen), "sonnet" fuer Standard-Tasks (neue Methoden, Tests, Refactoring), "opus" nur fuer sehr komplexe Architektur-Tasks</rule>
<rule name="effort">"low" fuer mechanische Tasks, "medium" fuer Standard, "high" fuer komplexe Logik</rule>
<rule name="test_level">"L1" wenn der Task mit Unit Tests/Lint verifiziert werden soll, "L2" wenn Integration Tests noetig sind, leer wenn kein Testing noetig</rule>
<rule name="assumptions">Liste alle Annahmen ueber die Codebase auf (z.B. "Tests laufen mit pytest")</rule>
<rule name="out_of_scope">Liste explizit auf was NICHT gemacht werden soll</rule>
</rules>

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
