#!/usr/bin/env python3
"""
Outbid Dirigent – Executor
Führt Claude Code Prozesse aus für Business Rule Extraktion, Planning und Task-Ausführung.
"""

import os
import re
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from outbid_dirigent.logger import get_logger
from outbid_dirigent.oracle import Oracle, create_oracle
from outbid_dirigent.router import load_state, save_state, mark_step_complete
from outbid_dirigent.proteus_integration import ProteusIntegration, create_proteus_integration


@dataclass
class TaskResult:
    """Ergebnis einer Task-Ausführung."""
    task_id: str
    success: bool
    commit_hash: Optional[str]
    summary: str
    deviations: List[Dict]
    duration_seconds: float
    attempts: int


@dataclass
class Phase:
    """Eine Ausführungsphase."""
    id: str
    name: str
    tasks: List[Dict]


class Executor:
    """Führt alle Claude Code Operationen aus."""

    MAX_TASK_RETRIES = 3
    CLAUDE_TIMEOUT = 1800  # 30 Minuten pro Task

    def __init__(self, repo_path: str, spec_path: str, dry_run: bool = False, use_proteus: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.spec_path = Path(spec_path).resolve()
        self.use_proteus = use_proteus
        self.dry_run = dry_run
        self.logger = get_logger()
        self.oracle = create_oracle(str(self.repo_path))

        # Verzeichnisse sicherstellen
        self.dirigent_dir = self.repo_path / ".dirigent"
        self.summaries_dir = self.dirigent_dir / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

        # Spec-Inhalt laden
        self.spec_content = self.spec_path.read_text(encoding="utf-8")

    def _run_claude(self, prompt: str, timeout: int = None) -> Tuple[bool, str, str]:
        """
        Führt Claude Code mit einem Prompt aus.

        Returns:
            Tuple von (success, stdout, stderr)
        """
        if self.dry_run:
            self.logger.info("[DRY-RUN] Würde Claude Code ausführen")
            return True, "[DRY-RUN] Simulierte Ausgabe", ""

        timeout = timeout or self.CLAUDE_TIMEOUT

        try:
            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", "-p", prompt],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            success = result.returncode == 0
            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude Code Timeout nach {timeout}s")
            return False, "", f"Timeout nach {timeout} Sekunden"
        except FileNotFoundError:
            self.logger.error("Claude CLI nicht gefunden. Ist 'claude' installiert?")
            return False, "", "Claude CLI nicht gefunden"
        except Exception as e:
            self.logger.error(f"Claude Code Fehler: {e}")
            return False, "", str(e)

    def _get_latest_commit_hash(self) -> Optional[str]:
        """Holt den letzten Commit-Hash."""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%H"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _load_business_rules(self) -> Optional[str]:
        """Lädt Business Rules falls vorhanden."""
        rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        if rules_file.exists():
            return rules_file.read_text(encoding="utf-8")
        return None

    def _load_previous_summaries(self) -> str:
        """Lädt alle bisherigen Task-Summaries."""
        summaries = []
        for summary_file in sorted(self.summaries_dir.glob("*-SUMMARY.md")):
            task_id = summary_file.stem.replace("-SUMMARY", "")
            content = summary_file.read_text(encoding="utf-8")
            summaries.append(f"### Task {task_id}\n{content}")

        return "\n\n".join(summaries) if summaries else "Keine vorherigen Tasks."

    # ========================================
    # BUSINESS RULE EXTRACTION (Legacy Route)
    # ========================================

    def extract_business_rules(self) -> bool:
        """Extrahiert Business Rules aus der Codebase (für Legacy-Route)."""
        self.logger.extract_start()

        # Wenn Proteus aktiviert ist, nutze Proteus für tiefere Extraktion
        if self.use_proteus:
            return self._extract_with_proteus()

        # Primäre Sprache aus Analyse laden
        analysis_file = self.dirigent_dir / "ANALYSIS.json"
        language = "unbekannt"
        if analysis_file.exists():
            with open(analysis_file, encoding="utf-8") as f:
                analysis = json.load(f)
                language = analysis.get("primary_language", "unbekannt")

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

        success, stdout, stderr = self._run_claude(prompt, timeout=900)  # 15 Minuten

        if not success:
            self.logger.error(f"Business Rule Extraktion fehlgeschlagen: {stderr}")
            return False

        # Prüfe ob Datei erstellt wurde
        rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        if rules_file.exists():
            # Zähle Regeln (approximativ)
            content = rules_file.read_text(encoding="utf-8")
            rule_count = content.count("- ") + content.count("* ")
            self.logger.extract_done(rule_count)
            return True
        else:
            self.logger.error("BUSINESS_RULES.md wurde nicht erstellt")
            return False

    def _extract_with_proteus(self) -> bool:
        """Nutzt Proteus für tiefgehende Domain-Extraktion."""
        self.logger.info("Nutze Proteus für Domain-Extraktion...")

        proteus = create_proteus_integration(str(self.repo_path), self.dry_run)

        # Führe Proteus Extraktion durch
        if not proteus.run_full_extraction():
            self.logger.error("Proteus Extraktion fehlgeschlagen")
            return False

        # Zusammenfassung loggen
        summary = proteus.get_extraction_summary()
        self.logger.info(
            f"Proteus: {summary['fields_count']} Fields, "
            f"{summary['rules_count']} Rules, "
            f"{summary['events_count']} Events, "
            f"{summary['dependencies_count']} Dependencies"
        )

        # Erstelle auch BUSINESS_RULES.md für Kompatibilität
        self._create_business_rules_from_proteus(proteus)

        return True

    def _create_business_rules_from_proteus(self, proteus: ProteusIntegration):
        """Erstellt BUSINESS_RULES.md aus Proteus-Daten für Abwärtskompatibilität."""
        proteus_dir = self.repo_path / ".proteus"
        rules_content = [f"# Business Rules – {self.repo_path.name}\n"]
        rules_content.append("*Extrahiert mit Proteus*\n")

        # Arch einbinden
        arch_file = proteus_dir / "arch.md"
        if arch_file.exists():
            rules_content.append("## Architektur\n")
            rules_content.append(arch_file.read_text(encoding="utf-8")[:3000])
            rules_content.append("\n")

        # Rules einbinden
        rules_file = proteus_dir / "rules.json"
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    data = json.load(f)
                rules_content.append("## Business Rules\n")
                for rule in data.get("rules", []):
                    rules_content.append(f"- **{rule.get('name', 'Unknown')}**: {rule.get('description', '')}\n")
                    if rule.get('logic'):
                        rules_content.append(f"  - Logic: {rule.get('logic')}\n")
            except Exception:
                pass

        # Events einbinden
        events_file = proteus_dir / "events.json"
        if events_file.exists():
            try:
                with open(events_file) as f:
                    data = json.load(f)
                rules_content.append("\n## Domain Events\n")
                for event in data.get("events", []):
                    rules_content.append(f"- **{event.get('name', 'Unknown')}**: {event.get('trigger', '')}\n")
            except Exception:
                pass

        # Speichern
        business_rules_file = self.dirigent_dir / "BUSINESS_RULES.md"
        with open(business_rules_file, "w", encoding="utf-8") as f:
            f.write("".join(rules_content))

        self.logger.info("BUSINESS_RULES.md aus Proteus-Daten erstellt")

    # ========================================
    # QUICK SCAN (Hybrid Route)
    # ========================================

    def quick_scan(self) -> bool:
        """Schneller Scan der relevanten Dateien (für Hybrid-Route)."""
        self.logger.info("Starte Quick Scan...")

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

        success, stdout, stderr = self._run_claude(prompt, timeout=300)  # 5 Minuten

        if not success:
            self.logger.error(f"Quick Scan fehlgeschlagen: {stderr}")
            return False

        self.logger.info("Quick Scan abgeschlossen")
        return True

    # ========================================
    # PLANNING
    # ========================================

    def create_plan(self) -> bool:
        """Erstellt den Ausführungsplan."""
        self.logger.plan_start()

        # Zusätzlichen Kontext sammeln
        business_rules = self._load_business_rules()
        business_rules_context = ""
        if business_rules:
            business_rules_context = f"""
## Business Rules (müssen erhalten bleiben!)
{business_rules[:3000]}
{"... (truncated)" if len(business_rules) > 3000 else ""}
"""

        context_file = self.dirigent_dir / "CONTEXT.md"
        context_content = ""
        if context_file.exists():
            context_content = f"""
## Repo-Kontext
{context_file.read_text(encoding="utf-8")}
"""

        prompt = f"""Erstelle einen Ausführungsplan für dieses Feature.

# Spec
{self.spec_content}

{business_rules_context}
{context_content}

Erstelle die Datei .dirigent/PLAN.json mit diesem Format:
{{
  "title": "Feature-Titel",
  "summary": "Kurze Beschreibung was implementiert wird",
  "phases": [
    {{
      "id": "01",
      "name": "Phase-Name",
      "description": "Was in dieser Phase passiert",
      "tasks": [
        {{
          "id": "01-01",
          "name": "Task-Name",
          "description": "Detaillierte Beschreibung was zu tun ist",
          "files_to_create": ["liste/von/neuen/dateien.ext"],
          "files_to_modify": ["liste/von/existierenden/dateien.ext"],
          "depends_on": []
        }}
      ]
    }}
  ],
  "estimated_complexity": "low|medium|high",
  "risks": ["Liste von potentiellen Risiken"]
}}

Regeln:
- Maximal 4 Phasen
- Maximal 4 Tasks pro Phase
- Jeder Task ist atomar (macht genau eine Sache)
- Keine Abhängigkeiten zwischen Tasks innerhalb einer Phase
- Tasks müssen konkret und ausführbar sein
- Bei Legacy-Migration: Alle Business Rules müssen erhalten bleiben

Erstelle den Plan jetzt.
"""

        success, stdout, stderr = self._run_claude(prompt, timeout=1800)  # 30 Minuten

        if not success:
            self.logger.error(f"Plan-Erstellung fehlgeschlagen: {stderr}")
            return False

        # Plan laden und validieren
        plan_file = self.dirigent_dir / "PLAN.json"
        if not plan_file.exists():
            self.logger.error("PLAN.json wurde nicht erstellt")
            return False

        try:
            with open(plan_file, encoding="utf-8") as f:
                plan = json.load(f)

            phases = plan.get("phases", [])
            total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)
            phase_details = [
                {
                    "phase": int(p["id"]) if p["id"].isdigit() else p["id"],
                    "name": p["name"],
                    "taskCount": len(p.get("tasks", [])),
                }
                for p in phases
            ]
            self.logger.plan_done(len(phases), total_tasks, phase_details)
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"PLAN.json ist kein valides JSON: {e}")
            return False

    # ========================================
    # TASK EXECUTION
    # ========================================

    def execute_plan(self) -> bool:
        """Führt den kompletten Plan aus."""
        plan = self._load_plan()
        if not plan:
            self.logger.error("Kein Plan gefunden")
            return False

        state = self._load_or_init_state()

        for phase in plan.get("phases", []):
            phase_id = phase["id"]
            phase_name = phase["name"]
            phase_tasks = phase.get("tasks", [])
            phase_num = int(phase_id) if phase_id.isdigit() else phase_id

            # Prüfe ob Phase bereits abgeschlossen
            if phase_id in state.get("completed_phases", []):
                self.logger.skip(phase_id, "bereits abgeschlossen")
                continue

            self.logger.phase_start(phase_id, phase_name, len(phase_tasks))

            phase_deviation_count = 0
            phase_commit_count = 0
            phase_tasks_completed = 0

            for task in phase_tasks:
                task_id = task["id"]

                # Prüfe ob Task bereits abgeschlossen
                if task_id in state.get("completed_tasks", []):
                    self.logger.skip(task_id, "bereits abgeschlossen")
                    phase_tasks_completed += 1
                    continue

                result = self._execute_task(task, phase_num=phase_num)

                if result.success:
                    state["completed_tasks"].append(task_id)
                    save_state(str(self.repo_path), state)
                    phase_tasks_completed += 1
                    phase_deviation_count += len(result.deviations)
                    if result.commit_hash:
                        phase_commit_count += 1
                else:
                    # Task fehlgeschlagen nach allen Retries
                    state["failed_tasks"] = state.get("failed_tasks", [])
                    state["failed_tasks"].append({
                        "task_id": task_id,
                        "error": result.summary,
                        "attempts": result.attempts,
                    })
                    save_state(str(self.repo_path), state)

                    self.logger.stop(f"Task {task_id} fehlgeschlagen nach {result.attempts} Versuchen")
                    self.logger.error_json(
                        f"Task {task_id} fehlgeschlagen nach {result.attempts} Versuchen",
                        phase=phase_num, task_id=task_id, fatal=True,
                    )
                    self.logger.run_complete(success=False)
                    return False

            # Phase abgeschlossen
            state["completed_phases"] = state.get("completed_phases", [])
            state["completed_phases"].append(phase_id)
            save_state(str(self.repo_path), state)
            self.logger.phase_complete(
                phase_id, phase_name, phase_tasks_completed,
                phase_deviation_count, phase_commit_count,
            )

        self.logger.run_complete(success=True)
        return True

    def _execute_task(self, task: Dict, phase_num=None) -> TaskResult:
        """Führt einen einzelnen Task aus."""
        task_id = task["id"]
        task_name = task["name"]
        start_time = datetime.now()

        self.logger.task_start(task_id, task_name, phase=phase_num)

        # Vorherige Summaries laden
        previous_summaries = self._load_previous_summaries()

        # Business Rules laden falls vorhanden
        business_rules = self._load_business_rules()
        rules_context = ""
        if business_rules:
            rules_context = f"""
## Business Rules (MÜSSEN erhalten bleiben!)
{business_rules[:2000]}
"""

        prompt = f"""Du führst Task {task_id} aus: {task_name}

# Gesamt-Spec
{self.spec_content}

# Bisheriger Fortschritt
{previous_summaries}

# Dein Task
{task['description']}

Dateien zu erstellen: {', '.join(task.get('files_to_create', [])) or 'keine'}
Dateien zu modifizieren: {', '.join(task.get('files_to_modify', [])) or 'keine'}

{rules_context}

## Deviation Rules
Du MUSST diese Regeln befolgen:

1. **Bug gefunden**: Automatisch fixen, in Summary als "DEVIATION: Bug-Fix" dokumentieren
2. **Kritisches fehlt**: Hinzufügen, in Summary als "DEVIATION: Added Missing" dokumentieren
3. **Blocker entdeckt**: Beheben, in Summary als "DEVIATION: Resolved Blocker" dokumentieren
4. **Architektur-Frage**: STOPP – Frage für Oracle dokumentieren

## Nach Abschluss
1. Alle Änderungen committen:
   git add -A && git commit -m "feat({task_id}): {task_name}"

2. Summary erstellen in .dirigent/summaries/{task_id}-SUMMARY.md:
   # Task {task_id}: {task_name}

   ## Was wurde gemacht
   (Kurze Beschreibung)

   ## Geänderte Dateien
   - file1.ext: Beschreibung

   ## Deviations
   (Falls vorhanden)

   ## Nächste Schritte
   (Falls relevant für folgende Tasks)

Keine Rückfragen. Kein Warten. Durcharbeiten und committen.
"""

        for attempt in range(1, self.MAX_TASK_RETRIES + 1):
            if attempt > 1:
                self.logger.task_retry(task_id, attempt)

            success, stdout, stderr = self._run_claude(prompt)

            if success:
                # Commit-Hash holen
                commit_hash = self._get_latest_commit_hash()

                # Summary laden
                summary_file = self.summaries_dir / f"{task_id}-SUMMARY.md"
                summary = ""
                if summary_file.exists():
                    summary = summary_file.read_text(encoding="utf-8")

                # Deviations extrahieren
                deviations = self._extract_deviations(summary)
                for dev in deviations:
                    self.logger.deviation(dev["type"], dev["description"],
                                          task_id=task_id, phase=phase_num)

                duration = (datetime.now() - start_time).total_seconds()
                self.logger.task_done(task_id, commit_hash,
                                      task_name=task_name, phase=phase_num)

                return TaskResult(
                    task_id=task_id,
                    success=True,
                    commit_hash=commit_hash,
                    summary=summary,
                    deviations=deviations,
                    duration_seconds=duration,
                    attempts=attempt,
                )
            else:
                self.logger.task_failed(task_id, stderr[:200], attempt)

        # Alle Retries aufgebraucht
        duration = (datetime.now() - start_time).total_seconds()
        return TaskResult(
            task_id=task_id,
            success=False,
            commit_hash=None,
            summary=f"Fehlgeschlagen nach {self.MAX_TASK_RETRIES} Versuchen",
            deviations=[],
            duration_seconds=duration,
            attempts=self.MAX_TASK_RETRIES,
        )

    def _extract_deviations(self, summary: str) -> List[Dict]:
        """Extrahiert Deviations aus dem Summary."""
        deviations = []
        pattern = r"DEVIATION:\s*(\w+[-\w]*)\s*[:\-]?\s*(.+)"

        for match in re.finditer(pattern, summary, re.IGNORECASE):
            deviations.append({
                "type": match.group(1).strip(),
                "description": match.group(2).strip(),
            })

        return deviations

    def _load_plan(self) -> Optional[Dict]:
        """Lädt den Ausführungsplan."""
        plan_file = self.dirigent_dir / "PLAN.json"
        if plan_file.exists():
            with open(plan_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    def _load_or_init_state(self) -> Dict:
        """Lädt oder initialisiert den State."""
        state = load_state(str(self.repo_path))
        if not state:
            state = {
                "started_at": datetime.now().isoformat(),
                "completed_phases": [],
                "completed_tasks": [],
            }
        else:
            # Ensure required keys exist (for backwards compatibility)
            if "completed_phases" not in state:
                state["completed_phases"] = []
            if "completed_tasks" not in state:
                state["completed_tasks"] = []
        save_state(str(self.repo_path), state)
        return state

    # ========================================
    # SHIPPING
    # ========================================

    def ship(self) -> bool:
        """Erstellt Branch, pusht und erstellt PR."""
        plan = self._load_plan()
        spec_title = plan.get("title", "Dirigent Feature") if plan else "Dirigent Feature"

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        branch_name = f"feature/dirigent-{timestamp}"

        self.logger.ship_start(branch_name)

        if self.dry_run:
            self.logger.info("[DRY-RUN] Würde Branch erstellen und pushen")
            return True

        try:
            # Branch erstellen
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.logger.error(f"Branch-Erstellung fehlgeschlagen: {result.stderr}")
                return False

            # Push
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.logger.error(f"Push fehlgeschlagen: {result.stderr}")
                # Nicht kritisch - vielleicht kein Remote
                self.logger.ship_pushed(branch_name)
                return True

            # PR erstellen (falls gh verfügbar)
            if shutil.which("gh"):
                pr_body = self._generate_pr_body()

                result = subprocess.run(
                    [
                        "gh", "pr", "create",
                        "--title", f"feat: {spec_title}",
                        "--body", pr_body,
                        "--head", branch_name,
                    ],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    # PR URL extrahieren
                    pr_url = result.stdout.strip()
                    self.logger.ship_done(pr_url)
                else:
                    self.logger.info(f"PR-Erstellung fehlgeschlagen: {result.stderr}")
                    self.logger.ship_pushed(branch_name)
            else:
                self.logger.info("gh CLI nicht gefunden, PR manuell erstellen")
                self.logger.ship_pushed(branch_name)

            return True

        except Exception as e:
            self.logger.error(f"Shipping fehlgeschlagen: {e}")
            return False

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generiert das Abschlussprotokoll mit allen gesammelten Daten.
        Wird nach execute_plan() aufgerufen.
        """
        self.logger.info("Generiere Abschlussprotokoll...")

        plan = self._load_plan()
        plan_title = plan.get("title", "Feature") if plan else "Feature"

        # Sammle Task-Summaries
        summaries = []
        for summary_file in sorted(self.summaries_dir.glob("*-SUMMARY.md")):
            summaries.append(summary_file.read_text(encoding="utf-8"))

        # Oracle-Entscheidungen laden
        decisions = self.oracle.get_all_decisions()

        # Git diff für geänderte Dateien
        files_changed = self._get_files_changed()

        # Deviations sammeln
        deviations = self._collect_all_deviations(summaries)

        # Kosten-Totals vom Logger holen
        cost_totals = self.logger.get_cost_totals()

        # Markdown generieren
        markdown = self._generate_summary_markdown(
            plan_title, summaries, decisions, files_changed, deviations, cost_totals
        )

        # Event emittieren
        self.logger.summary(
            markdown=markdown,
            files_changed=files_changed,
            decisions=[{
                "question": d["question"][:200],
                "decision": d["decision"],
                "reason": d["reason"]
            } for d in decisions],
            deviations=deviations,
            total_cost_cents=cost_totals["total_cost_cents"],
            total_input_tokens=cost_totals["total_input_tokens"],
            total_output_tokens=cost_totals["total_output_tokens"],
        )

        return {
            "markdown": markdown,
            "files_changed": files_changed,
            "decisions": decisions,
            "deviations": deviations,
            "cost_totals": cost_totals,
        }

    def _get_files_changed(self) -> List[Dict]:
        """Holt geänderte Dateien via git diff."""
        try:
            # Anzahl Commits aus dem Plan ermitteln
            result = subprocess.run(
                ["git", "diff", "--numstat", "HEAD~20..HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            files = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) == 3:
                        added = int(parts[0]) if parts[0] != '-' else 0
                        removed = int(parts[1]) if parts[1] != '-' else 0
                        files.append({
                            "path": parts[2],
                            "lines_added": added,
                            "lines_removed": removed,
                        })
            return files
        except Exception as e:
            self.logger.debug(f"Git diff Fehler: {e}")
            return []

    def _collect_all_deviations(self, summaries: List[str]) -> List[Dict]:
        """Sammelt alle Deviations aus den Task-Summaries."""
        all_deviations = []
        for summary in summaries:
            deviations = self._extract_deviations(summary)
            all_deviations.extend(deviations)
        return all_deviations

    def _generate_summary_markdown(
        self,
        title: str,
        summaries: List[str],
        decisions: List[Dict],
        files: List[Dict],
        deviations: List[Dict],
        cost_totals: Dict,
    ) -> str:
        """Erstellt lesbares Abschlussprotokoll."""
        plan = self._load_plan()
        phases_count = len(plan.get("phases", [])) if plan else 0
        tasks_count = sum(len(p.get("tasks", [])) for p in plan.get("phases", [])) if plan else 0

        md = [f"# Abschlussprotokoll: {title}\n"]
        md.append(f"**Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

        # Übersicht
        md.append("## Übersicht\n")
        cost_usd = cost_totals["total_cost_cents"] / 100
        md.append(f"- **Phasen:** {phases_count}")
        md.append(f"- **Tasks:** {tasks_count}")
        md.append(f"- **Dateien geändert:** {len(files)}")
        md.append(f"- **Deviations:** {len(deviations)}")
        md.append(f"- **Oracle-Entscheidungen:** {len(decisions)}")
        md.append(f"- **API-Kosten:** ${cost_usd:.2f}")
        md.append(f"- **Tokens:** {cost_totals['total_input_tokens']:,} in / {cost_totals['total_output_tokens']:,} out\n")

        # Geänderte Dateien
        if files:
            md.append("## Geänderte Dateien\n")
            for f in files[:30]:  # Max 30
                md.append(f"- `{f['path']}` (+{f['lines_added']}/-{f['lines_removed']})")
            if len(files) > 30:
                md.append(f"- ... und {len(files) - 30} weitere Dateien")
            md.append("")

        # Oracle-Entscheidungen
        if decisions:
            md.append("## Oracle-Entscheidungen\n")
            for d in decisions[:15]:  # Max 15
                question_short = d['question'][:100] + "..." if len(d['question']) > 100 else d['question']
                md.append(f"**Q:** {question_short}")
                md.append(f"**A:** {d['decision']}")
                md.append(f"*{d['reason']}*\n")
            if len(decisions) > 15:
                md.append(f"... und {len(decisions) - 15} weitere Entscheidungen\n")

        # Deviations
        if deviations:
            md.append("## Deviations\n")
            for dev in deviations:
                md.append(f"- **{dev['type']}:** {dev['description']}")
            md.append("")

        # Task-Summaries (komprimiert)
        if summaries:
            md.append("## Task-Details\n")
            for i, summary in enumerate(summaries[:10], 1):
                # Nur erste Zeilen pro Summary
                lines = summary.strip().split("\n")
                title_line = lines[0] if lines else f"Task {i}"
                md.append(f"### {title_line}")
                # Nur "Was wurde gemacht" Sektion
                match = re.search(r"## Was wurde gemacht\n(.+?)(?=\n##|\Z)", summary, re.DOTALL)
                if match:
                    md.append(match.group(1).strip()[:300])
                md.append("")
            if len(summaries) > 10:
                md.append(f"... und {len(summaries) - 10} weitere Tasks\n")

        return "\n".join(md)

    def _generate_pr_body(self) -> str:
        """Generiert den PR Body."""
        plan = self._load_plan()

        body_parts = [
            "## Summary",
            plan.get("summary", "Automatisch erstellt vom Outbid Dirigenten.") if plan else "Automatisch erstellt vom Outbid Dirigenten.",
            "",
            "## Changes",
        ]

        # Summaries einbinden
        for summary_file in sorted(self.summaries_dir.glob("*-SUMMARY.md")):
            content = summary_file.read_text(encoding="utf-8")
            # Nur "Was wurde gemacht" Sektion extrahieren
            match = re.search(r"## Was wurde gemacht\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
            if match:
                body_parts.append(f"- {match.group(1).strip()}")

        body_parts.extend([
            "",
            "---",
            "*Automatisch erstellt vom Outbid Dirigenten*",
        ])

        return "\n".join(body_parts)


def create_executor(repo_path: str, spec_path: str, dry_run: bool = False, use_proteus: bool = False) -> Executor:
    """Factory-Funktion für Executor-Instanz."""
    return Executor(repo_path, spec_path, dry_run, use_proteus)
