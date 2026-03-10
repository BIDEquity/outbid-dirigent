#!/usr/bin/env python3
"""
Outbid Dirigent – Proteus Integration
Nutzt Proteus für tiefgehende Domain-Extraktion statt einfacher Business Rule Extraktion.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

from logger import get_logger


class ProteusIntegration:
    """
    Integriert Proteus in den Dirigent für bessere Domain-Extraktion.

    Proteus Phasen:
    1. Survey - Architektur-Profil erstellen
    2. Extract Fields - Datenfelder extrahieren
    3. Extract Rules - Business Rules extrahieren
    4. Extract Events - Domain Events extrahieren
    5. Map Dependencies - CRUD Dependencies mappen
    6. Verify - Wissen verifizieren (wird übersprungen im headless mode)
    """

    PROTEUS_TIMEOUT = 1800  # 30 Minuten pro Phase

    def __init__(self, repo_path: str, dry_run: bool = False):
        self.repo_path = Path(repo_path).resolve()
        self.dry_run = dry_run
        self.logger = get_logger()
        self.proteus_dir = self.repo_path / ".proteus"

    def is_proteus_available(self) -> bool:
        """Prüft ob Proteus als Claude Code Plugin verfügbar ist."""
        try:
            # Prüfe ob uvx verfügbar ist (für Proteus MCP)
            result = subprocess.run(
                ["which", "uvx"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                self.logger.info("uvx nicht gefunden - Proteus nicht verfügbar")
                return False

            # Prüfe ob Proteus Plugin installiert ist
            result = subprocess.run(
                ["claude", "plugin", "list"],
                capture_output=True,
                text=True,
            )
            if "proteus" in result.stdout.lower():
                return True

            self.logger.info("Proteus Plugin nicht installiert")
            return False

        except Exception as e:
            self.logger.debug(f"Proteus Check fehlgeschlagen: {e}")
            return False

    def install_proteus(self) -> bool:
        """Installiert Proteus Plugin falls nicht vorhanden."""
        self.logger.info("Installiere Proteus Plugin...")

        try:
            # Marketplace hinzufügen
            subprocess.run(
                ["claude", "plugin", "marketplace", "add", "BIDEquity/proteus-alpha"],
                capture_output=True,
                text=True,
            )

            # Plugin installieren
            result = subprocess.run(
                ["claude", "plugin", "install", "proteus@proteus-marketplace", "--scope", "user"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.logger.info("Proteus Plugin installiert")
                return True
            else:
                self.logger.error(f"Proteus Installation fehlgeschlagen: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Proteus Installation Fehler: {e}")
            return False

    def _run_claude_with_proteus(self, prompt: str, timeout: int = None) -> tuple[bool, str, str]:
        """Führt Claude Code mit Proteus Plugin aus."""
        if self.dry_run:
            self.logger.info("[DRY-RUN] Würde Claude mit Proteus ausführen")
            return True, "[DRY-RUN]", ""

        timeout = timeout or self.PROTEUS_TIMEOUT

        try:
            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", "-p", prompt],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return result.returncode == 0, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            self.logger.error(f"Proteus Timeout nach {timeout}s")
            return False, "", f"Timeout nach {timeout}s"
        except Exception as e:
            self.logger.error(f"Proteus Fehler: {e}")
            return False, "", str(e)

    def run_survey(self) -> bool:
        """Phase 1: Survey - Architektur-Profil erstellen."""
        self.logger.info("Proteus Phase 1: Survey...")

        prompt = f"""Führe eine Proteus Survey auf diesem Repository durch.

Erstelle das Verzeichnis .proteus/ falls es nicht existiert.

Analysiere systematisch:
- Entry Points und Routing
- Data Models, ORM, Datenbank-Schemas
- Service/Business Logic Layers
- Externe API Clients
- Konfiguration

Erstelle .proteus/arch.md mit:
- Projekt-Beschreibung
- Core Features
- Technology Stack
- Architektur-Pattern
- Data Access (DB + externe APIs)
- Business Logic Hotspots
- Refactoring Opportunities

Arbeite gründlich durch die gesamte Codebase.
Keine Rückfragen - dokumentiere was du findest.
"""

        success, stdout, stderr = self._run_claude_with_proteus(prompt)

        if success and (self.proteus_dir / "arch.md").exists():
            self.logger.info("Proteus Survey abgeschlossen")
            self._update_pipeline(1, "survey")
            return True
        else:
            self.logger.error(f"Proteus Survey fehlgeschlagen: {stderr}")
            return False

    def run_extract_fields(self) -> bool:
        """Phase 2: Extract Fields - Datenfelder extrahieren."""
        self.logger.info("Proteus Phase 2: Extract Fields...")

        prompt = """Extrahiere alle Datenfelder aus der Codebase.

Nutze die Proteus MCP Tools falls verfügbar:
- mcp__proteus__create_field für jedes gefundene Feld

Falls MCP nicht verfügbar, erstelle .proteus/fields.json:
{{
  "fields": [
    {{
      "name": "field_name",
      "entity": "EntityName",
      "type": "string|int|date|...",
      "nullable": true|false,
      "description": "Was dieses Feld bedeutet",
      "source_location": "path/to/file.java:123"
    }}
  ]
}}

Analysiere:
- Datenbank-Entities/Models
- API Request/Response Objekte
- DTOs und Value Objects
- Konfigurationsfelder

Sei gründlich - jedes Feld zählt.
"""

        success, stdout, stderr = self._run_claude_with_proteus(prompt)

        if success:
            self.logger.info("Proteus Fields Extraktion abgeschlossen")
            self._update_pipeline(2, "extract-fields")
            return True
        else:
            self.logger.error(f"Proteus Fields Extraktion fehlgeschlagen: {stderr}")
            return False

    def run_extract_rules(self) -> bool:
        """Phase 3: Extract Rules - Business Rules extrahieren."""
        self.logger.info("Proteus Phase 3: Extract Rules...")

        prompt = """Extrahiere alle Business Rules aus der Codebase.

Nutze die Proteus MCP Tools falls verfügbar:
- mcp__proteus__create_domain für Bounded Contexts
- mcp__proteus__create_business_rule für jede Regel

Falls MCP nicht verfügbar, erstelle .proteus/rules.json:
{{
  "domains": [
    {{
      "name": "DomainName",
      "description": "Was diese Domain macht"
    }}
  ],
  "rules": [
    {{
      "id": "RULE-001",
      "domain": "DomainName",
      "name": "Regel-Name",
      "description": "Was diese Regel tut",
      "logic": "Pseudo-Code oder natürliche Sprache",
      "source_location": "path/to/file.java:123",
      "confidence": "high|medium|low"
    }}
  ]
}}

Suche nach:
- Validierungen
- Berechnungen
- Constraints
- Workflows/State Machines
- Berechtigungsprüfungen

Dokumentiere JEDE Regel die du findest.
"""

        success, stdout, stderr = self._run_claude_with_proteus(prompt)

        if success:
            self.logger.info("Proteus Rules Extraktion abgeschlossen")
            self._update_pipeline(3, "extract-rules")
            return True
        else:
            self.logger.error(f"Proteus Rules Extraktion fehlgeschlagen: {stderr}")
            return False

    def run_extract_events(self) -> bool:
        """Phase 4: Extract Events - Domain Events extrahieren."""
        self.logger.info("Proteus Phase 4: Extract Events...")

        prompt = """Extrahiere alle Domain Events aus der Codebase.

Nutze die Proteus MCP Tools falls verfügbar:
- mcp__proteus__create_domain_event für jedes Event

Falls MCP nicht verfügbar, erstelle .proteus/events.json:
{{
  "events": [
    {{
      "name": "EventName",
      "domain": "DomainName",
      "trigger": "Was löst dieses Event aus",
      "consequences": ["Was passiert danach"],
      "fields_read": ["field1", "field2"],
      "fields_written": ["field3"],
      "source_location": "path/to/file.java:123"
    }}
  ]
}}

Suche nach:
- Event Publishing (ApplicationEventPublisher, etc.)
- Callbacks und Hooks
- State Changes
- Side Effects
- Notifications/Emails
- Audit Logging

Dokumentiere den kompletten Event Flow.
"""

        success, stdout, stderr = self._run_claude_with_proteus(prompt)

        if success:
            self.logger.info("Proteus Events Extraktion abgeschlossen")
            self._update_pipeline(4, "extract-events")
            return True
        else:
            self.logger.error(f"Proteus Events Extraktion fehlgeschlagen: {stderr}")
            return False

    def run_map_dependencies(self) -> bool:
        """Phase 5: Map Dependencies - CRUD Dependencies mappen."""
        self.logger.info("Proteus Phase 5: Map Dependencies...")

        prompt = """Mappe die CRUD Dependencies zwischen Rules und Fields.

Nutze die Proteus MCP Tools falls verfügbar:
- mcp__proteus__create_field_dependency

Falls MCP nicht verfügbar, erstelle .proteus/dependencies.json:
{{
  "dependencies": [
    {{
      "rule_id": "RULE-001",
      "field": "field_name",
      "operation": "CREATE|READ|UPDATE|DELETE",
      "source_location": "path/to/file.java:123"
    }}
  ]
}}

Analysiere für jede Business Rule:
- Welche Felder werden gelesen?
- Welche Felder werden geschrieben?
- Welche Felder werden validiert?

Diese Dependency Map ist kritisch für die Migration.
"""

        success, stdout, stderr = self._run_claude_with_proteus(prompt)

        if success:
            self.logger.info("Proteus Dependencies Mapping abgeschlossen")
            self._update_pipeline(5, "map-dependencies")
            return True
        else:
            self.logger.error(f"Proteus Dependencies Mapping fehlgeschlagen: {stderr}")
            return False

    def _update_pipeline(self, phase: int, name: str):
        """Aktualisiert die Pipeline-Status Datei."""
        self.proteus_dir.mkdir(parents=True, exist_ok=True)
        pipeline_file = self.proteus_dir / "pipeline.json"

        data = {
            "phase": phase,
            "name": name,
            "completed_at": datetime.now().isoformat(),
        }

        with open(pipeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def run_full_extraction(self) -> bool:
        """
        Führt die komplette Proteus Extraktion durch (Phasen 1-5).
        Phase 6 (Verify) wird im headless mode übersprungen.
        """
        self.logger.info("Starte Proteus Extraktion...")

        phases = [
            ("Survey", self.run_survey),
            ("Extract Fields", self.run_extract_fields),
            ("Extract Rules", self.run_extract_rules),
            ("Extract Events", self.run_extract_events),
            ("Map Dependencies", self.run_map_dependencies),
        ]

        for phase_name, phase_func in phases:
            self.logger.info(f"Proteus: {phase_name}...")
            if not phase_func():
                self.logger.error(f"Proteus {phase_name} fehlgeschlagen")
                return False

        self.logger.info("Proteus Extraktion komplett")
        return True

    def get_extraction_summary(self) -> Dict:
        """Gibt eine Zusammenfassung der Proteus-Extraktion zurück."""
        summary = {
            "arch_exists": (self.proteus_dir / "arch.md").exists(),
            "fields_count": 0,
            "rules_count": 0,
            "events_count": 0,
            "dependencies_count": 0,
        }

        # Fields zählen
        fields_file = self.proteus_dir / "fields.json"
        if fields_file.exists():
            try:
                with open(fields_file) as f:
                    data = json.load(f)
                    summary["fields_count"] = len(data.get("fields", []))
            except Exception:
                pass

        # Rules zählen
        rules_file = self.proteus_dir / "rules.json"
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    data = json.load(f)
                    summary["rules_count"] = len(data.get("rules", []))
            except Exception:
                pass

        # Events zählen
        events_file = self.proteus_dir / "events.json"
        if events_file.exists():
            try:
                with open(events_file) as f:
                    data = json.load(f)
                    summary["events_count"] = len(data.get("events", []))
            except Exception:
                pass

        # Dependencies zählen
        deps_file = self.proteus_dir / "dependencies.json"
        if deps_file.exists():
            try:
                with open(deps_file) as f:
                    data = json.load(f)
                    summary["dependencies_count"] = len(data.get("dependencies", []))
            except Exception:
                pass

        return summary

    def get_context_for_task(self, task_description: str) -> str:
        """
        Lädt relevanten Proteus-Kontext für einen Task.
        Wird während der Task-Ausführung verwendet.
        """
        context_parts = []

        # Arch laden
        arch_file = self.proteus_dir / "arch.md"
        if arch_file.exists():
            arch_content = arch_file.read_text(encoding="utf-8")
            # Nur die ersten 2000 Zeichen
            if len(arch_content) > 2000:
                arch_content = arch_content[:2000] + "\n... (truncated)"
            context_parts.append(f"## Architecture\n{arch_content}")

        # Relevante Rules laden (basierend auf Task-Beschreibung)
        rules_file = self.proteus_dir / "rules.json"
        if rules_file.exists():
            try:
                with open(rules_file) as f:
                    data = json.load(f)
                    rules = data.get("rules", [])
                    # Alle Rules als Kontext (könnte gefiltert werden)
                    if rules:
                        rules_text = "\n".join([
                            f"- [{r.get('id', 'N/A')}] {r.get('name', 'Unknown')}: {r.get('description', '')}"
                            for r in rules[:20]  # Max 20 Rules
                        ])
                        context_parts.append(f"## Business Rules\n{rules_text}")
            except Exception:
                pass

        return "\n\n".join(context_parts)


def create_proteus_integration(repo_path: str, dry_run: bool = False) -> ProteusIntegration:
    """Factory-Funktion für ProteusIntegration."""
    return ProteusIntegration(repo_path, dry_run)
