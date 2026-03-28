#!/usr/bin/env python3
"""
Outbid Dirigent – Router
Definiert die Ausführungspfade (Greenfield, Legacy, Hybrid) und deren Schritte.
"""

import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

from outbid_dirigent.analyzer import AnalysisResult
from outbid_dirigent.logger import get_logger


class RouteType(Enum):
    GREENFIELD = "greenfield"
    LEGACY = "legacy"
    HYBRID = "hybrid"


class StepType(Enum):
    INIT = "init"
    BUSINESS_RULE_EXTRACTION = "business_rule_extraction"
    QUICK_SCAN = "quick_scan"
    MANIFEST_GENERATION = "manifest_generation"
    PLANNING = "planning"
    EXECUTION = "execution"
    TEST = "test"
    SHIP = "ship"


@dataclass
class RouteStep:
    """Ein einzelner Schritt im Ausführungsplan."""
    step_type: StepType
    name: str
    description: str
    required: bool = True


@dataclass
class Route:
    """Der komplette Ausführungsplan."""
    route_type: RouteType
    reason: str
    steps: List[RouteStep]
    estimated_tasks: int
    oracle_needed: bool
    repo_context_needed: bool


class Router:
    """Bestimmt den Ausführungspfad basierend auf der Analyse."""

    # Definitionen der Pfade
    GREENFIELD_STEPS = [
        RouteStep(
            step_type=StepType.INIT,
            name="Init Phase",
            description="Bootstrap dev environment, seed data, configure e2e credentials",
            required=False,
        ),
        RouteStep(
            step_type=StepType.MANIFEST_GENERATION,
            name="Test-Manifest Generierung",
            description="3x Sonnet analysiert Test-Infrastruktur, Haiku konsolidiert",
            required=False,
        ),
        RouteStep(
            step_type=StepType.PLANNING,
            name="Planung",
            description="Claude Code analysiert Repo-Struktur und erstellt Ausführungsplan",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Ausführung",
            description="Tasks werden sequentiell ausgeführt mit frischem Kontext pro Task",
        ),
        RouteStep(
            step_type=StepType.TEST,
            name="Test Suite",
            description="Volle Test-Suite aus Test-Manifest ausführen",
            required=False,
        ),
        RouteStep(
            step_type=StepType.SHIP,
            name="Shipping",
            description="Branch erstellen, Push, PR erstellen",
        ),
    ]

    LEGACY_STEPS = [
        RouteStep(
            step_type=StepType.INIT,
            name="Init Phase",
            description="Bootstrap dev environment, seed data, configure e2e credentials",
            required=False,
        ),
        RouteStep(
            step_type=StepType.BUSINESS_RULE_EXTRACTION,
            name="Business Rule Extraktion",
            description="Claude Code liest komplette Codebase und extrahiert alle Business Rules",
        ),
        RouteStep(
            step_type=StepType.MANIFEST_GENERATION,
            name="Test-Manifest Generierung",
            description="3x Sonnet analysiert Test-Infrastruktur, Haiku konsolidiert",
            required=False,
        ),
        RouteStep(
            step_type=StepType.PLANNING,
            name="Planung mit Guardrails",
            description="Plan erstellen der BUSINESS_RULES.md als Kontext nutzt",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Ausführung mit Rule-Check",
            description="Tasks ausführen mit Business Rule Verification nach jedem Task",
        ),
        RouteStep(
            step_type=StepType.TEST,
            name="Test Suite",
            description="Volle Test-Suite aus Test-Manifest ausführen",
            required=False,
        ),
        RouteStep(
            step_type=StepType.SHIP,
            name="Shipping",
            description="Branch erstellen, Push, PR erstellen",
        ),
    ]

    HYBRID_STEPS = [
        RouteStep(
            step_type=StepType.INIT,
            name="Init Phase",
            description="Bootstrap dev environment, seed data, configure e2e credentials",
            required=False,
        ),
        RouteStep(
            step_type=StepType.QUICK_SCAN,
            name="Quick Scan",
            description="Claude Code analysiert nur die zum Feature relevanten Dateien",
        ),
        RouteStep(
            step_type=StepType.MANIFEST_GENERATION,
            name="Test-Manifest Generierung",
            description="3x Sonnet analysiert Test-Infrastruktur, Haiku konsolidiert",
            required=False,
        ),
        RouteStep(
            step_type=StepType.PLANNING,
            name="Planung mit Kontext",
            description="Plan erstellen mit Repo-Kontext",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Ausführung",
            description="Tasks ausführen mit Repo-Kontext",
        ),
        RouteStep(
            step_type=StepType.TEST,
            name="Test Suite",
            description="Volle Test-Suite aus Test-Manifest ausführen",
            required=False,
        ),
        RouteStep(
            step_type=StepType.SHIP,
            name="Shipping",
            description="Branch erstellen, Push, PR erstellen",
        ),
    ]

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.logger = get_logger()

    def determine_route(self, analysis) -> Route:
        """Bestimmt den optimalen Ausführungspfad."""

        # Handle both AnalysisResult object and dict (from cache)
        if isinstance(analysis, dict):
            route_str = analysis.get("route", "hybrid")
            route_reason = analysis.get("route_reason", "")
            estimated_scope = analysis.get("estimated_scope", "medium")
            file_count = analysis.get("file_count", 0)
            commit_count = analysis.get("commit_count", 0)
        else:
            route_str = analysis.route
            route_reason = analysis.route_reason
            estimated_scope = analysis.spec.estimated_scope
            file_count = analysis.repo.file_count
            commit_count = analysis.repo.commit_count

        route_type = RouteType(route_str)

        if route_type == RouteType.GREENFIELD:
            return self._build_route_from_data(
                RouteType.GREENFIELD, route_reason, estimated_scope,
                file_count, commit_count, self.GREENFIELD_STEPS
            )
        elif route_type == RouteType.LEGACY:
            return self._build_route_from_data(
                RouteType.LEGACY, route_reason, estimated_scope,
                file_count, commit_count, self.LEGACY_STEPS
            )
        else:
            return self._build_route_from_data(
                RouteType.HYBRID, route_reason, estimated_scope,
                file_count, commit_count, self.HYBRID_STEPS
            )

    def _build_route_from_data(self, route_type: RouteType, reason: str,
                                estimated_scope: str, file_count: int,
                                commit_count: int, steps: list) -> Route:
        """Baut eine Route aus den Daten."""
        estimated_tasks = self._estimate_tasks(estimated_scope)

        return Route(
            route_type=route_type,
            reason=reason,
            steps=steps.copy(),
            estimated_tasks=estimated_tasks,
            oracle_needed=route_type == RouteType.LEGACY or commit_count > 200,
            repo_context_needed=file_count > 10,
        )


    def _estimate_tasks(self, scope: str) -> int:
        """Schätzt die Anzahl der Tasks basierend auf dem Scope."""
        estimates = {
            "small": 4,
            "medium": 8,
            "large": 12,
        }
        return estimates.get(scope, 6)

    def save_route(self, route: Route):
        """Speichert die Route in .dirigent/ROUTE.json."""
        dirigent_dir = self.repo_path / ".dirigent"
        dirigent_dir.mkdir(parents=True, exist_ok=True)

        route_file = dirigent_dir / "ROUTE.json"

        data = {
            "route": route.route_type.value,
            "reason": route.reason,
            "steps": [step.step_type.value for step in route.steps],
            "step_details": [
                {
                    "type": step.step_type.value,
                    "name": step.name,
                    "description": step.description,
                    "required": step.required,
                }
                for step in route.steps
            ],
            "estimated_tasks": route.estimated_tasks,
            "oracle_needed": route.oracle_needed,
            "repo_context_needed": route.repo_context_needed,
            "created_at": datetime.now().isoformat(),
        }

        with open(route_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.debug(f"Route gespeichert in {route_file}")


def load_route(repo_path: str) -> Optional[Dict]:
    """Lädt eine existierende Route."""
    route_file = Path(repo_path) / ".dirigent" / "ROUTE.json"
    if route_file.exists():
        with open(route_file, encoding="utf-8") as f:
            return json.load(f)
    return None


def get_next_step(repo_path: str) -> Optional[str]:
    """Ermittelt den nächsten auszuführenden Schritt."""
    state = load_state(repo_path)
    route = load_route(repo_path)

    if not route:
        return None

    if not state:
        return route["steps"][0]

    completed_steps = state.get("completed_steps", [])

    for step in route["steps"]:
        if step not in completed_steps:
            return step

    return None  # Alle Schritte abgeschlossen


def load_state(repo_path: str) -> Optional[Dict]:
    """Lädt den aktuellen State."""
    state_file = Path(repo_path) / ".dirigent" / "STATE.json"
    if state_file.exists():
        with open(state_file, encoding="utf-8") as f:
            return json.load(f)
    return None


def save_state(repo_path: str, state: Dict):
    """Speichert den aktuellen State."""
    state_file = Path(repo_path) / ".dirigent" / "STATE.json"
    state["updated_at"] = datetime.now().isoformat()

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def mark_step_complete(repo_path: str, step: str):
    """Markiert einen Schritt als abgeschlossen."""
    state = load_state(repo_path) or {"completed_steps": [], "started_at": datetime.now().isoformat()}

    if "completed_steps" not in state:
        state["completed_steps"] = []

    if step not in state["completed_steps"]:
        state["completed_steps"].append(step)

    save_state(repo_path, state)
