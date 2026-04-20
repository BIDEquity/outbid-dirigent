#!/usr/bin/env python3
"""
Outbid Dirigent – Router
Definiert die Ausführungspfade (Greenfield, Legacy, Hybrid, Testability, Tracking) und deren Schritte.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ValidationError

from outbid_dirigent.logger import get_logger


class RouteType(Enum):
    QUICK = "quick"
    GREENFIELD = "greenfield"
    LEGACY = "legacy"
    HYBRID = "hybrid"
    TESTABILITY = "testability"
    TRACKING = "tracking"


class StepType(Enum):
    INIT = "init"
    GREENFIELD_SCAFFOLD = "greenfield_scaffold"
    BUSINESS_RULE_EXTRACTION = "business_rule_extraction"
    QUICK_SCAN = "quick_scan"
    INCREASE_TESTABILITY = "increase_testability"
    ADD_TRACKING = "add_tracking"
    PLANNING = "planning"
    EXECUTION = "execution"
    ENTROPY_MINIMIZATION = "entropy_minimization"
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


class RouteRecord(BaseModel):
    route: str
    reason: str
    steps: list[str]
    step_details: list[dict]
    estimated_tasks: int
    oracle_needed: bool
    repo_context_needed: bool
    created_at: str


class StateRecord(BaseModel):
    completed_steps: list[str]
    started_at: str
    updated_at: str = ""


class Router:
    """Bestimmt den Ausführungspfad basierend auf der Analyse."""

    # Definitionen der Pfade
    QUICK_STEPS = [
        RouteStep(
            step_type=StepType.PLANNING,
            name="Planung",
            description="Kurze Analyse und Ausführungsplan für kleine Änderung",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Ausführung",
            description="Änderung in einem Durchlauf umsetzen",
        ),
        RouteStep(
            step_type=StepType.SHIP,
            name="Shipping",
            description="Branch erstellen, Push, PR erstellen",
        ),
    ]

    GREENFIELD_STEPS = [
        RouteStep(
            step_type=StepType.GREENFIELD_SCAFFOLD,
            name="Greenfield Scaffold",
            description="Pick stack, scaffold project, create ARCHITECTURE.md and start.sh",
            required=True,
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
            step_type=StepType.ENTROPY_MINIMIZATION,
            name="Entropy Minimization",
            description="Align docs, remove dead code, resolve contradictions introduced during execution",
            required=False,
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
            step_type=StepType.ENTROPY_MINIMIZATION,
            name="Entropy Minimization",
            description="Align docs, remove dead code, resolve contradictions introduced during execution",
            required=False,
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
            step_type=StepType.ENTROPY_MINIMIZATION,
            name="Entropy Minimization",
            description="Align docs, remove dead code, resolve contradictions introduced during execution",
            required=False,
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

    TESTABILITY_STEPS = [
        RouteStep(
            step_type=StepType.INIT,
            name="Init Phase",
            description="Bootstrap dev environment, assess current testability",
            required=True,
        ),
        RouteStep(
            step_type=StepType.INCREASE_TESTABILITY,
            name="Testability-Analyse",
            description="Analyse testability gaps and produce recommendations",
        ),
        RouteStep(
            step_type=StepType.PLANNING,
            name="Testability Plan",
            description="Plan tasks to implement testability recommendations",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Testability verbessern",
            description="Implement test infrastructure, seed data, health checks, e2e setup",
        ),
        RouteStep(
            step_type=StepType.ENTROPY_MINIMIZATION,
            name="Entropy Minimization",
            description="Align docs, remove dead code, resolve contradictions introduced during execution",
            required=False,
        ),
        RouteStep(
            step_type=StepType.TEST,
            name="Verification",
            description="Run new test infrastructure to verify it works",
            required=False,
        ),
        RouteStep(
            step_type=StepType.SHIP,
            name="Shipping",
            description="Branch erstellen, Push, PR erstellen",
        ),
    ]

    TRACKING_STEPS = [
        RouteStep(
            step_type=StepType.INIT,
            name="Init Phase",
            description="Bootstrap dev environment, detect existing analytics",
            required=False,
        ),
        RouteStep(
            step_type=StepType.QUICK_SCAN,
            name="Tracking Scan",
            description="Scan for existing analytics, identify key user flows to track",
        ),
        RouteStep(
            step_type=StepType.ADD_TRACKING,
            name="PostHog Setup",
            description="Install PostHog SDK and identify tracking points",
        ),
        RouteStep(
            step_type=StepType.PLANNING,
            name="Tracking Plan",
            description="Plan event instrumentation across identified user flows",
        ),
        RouteStep(
            step_type=StepType.EXECUTION,
            name="Tracking implementieren",
            description="Add PostHog initialization, event tracking, feature flags, and user identification",
        ),
        RouteStep(
            step_type=StepType.ENTROPY_MINIMIZATION,
            name="Entropy Minimization",
            description="Align docs, remove dead code, resolve contradictions introduced during execution",
            required=False,
        ),
        RouteStep(
            step_type=StepType.TEST,
            name="Verification",
            description="Verify tracking events fire correctly",
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

        steps_map = {
            RouteType.QUICK: self.QUICK_STEPS,
            RouteType.GREENFIELD: self.GREENFIELD_STEPS,
            RouteType.LEGACY: self.LEGACY_STEPS,
            RouteType.HYBRID: self.HYBRID_STEPS,
            RouteType.TESTABILITY: self.TESTABILITY_STEPS,
            RouteType.TRACKING: self.TRACKING_STEPS,
        }
        steps = steps_map.get(route_type, self.HYBRID_STEPS)

        return self._build_route_from_data(
            route_type,
            route_reason,
            estimated_scope,
            file_count,
            commit_count,
            steps,
        )

    def _build_route_from_data(
        self,
        route_type: RouteType,
        reason: str,
        estimated_scope: str,
        file_count: int,
        commit_count: int,
        steps: list,
    ) -> Route:
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

    def save_route(self, route: Route, dirigent_dir: Optional[Path] = None):
        """Speichert die Route in ROUTE.json."""
        target_dir = dirigent_dir or (self.repo_path / ".dirigent")
        target_dir.mkdir(parents=True, exist_ok=True)

        route_file = target_dir / "ROUTE.json"

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


def load_route(repo_path: str, dirigent_dir: Optional[Path] = None) -> Optional[Dict]:
    """Lädt eine existierende Route."""
    route_file = (dirigent_dir or Path(repo_path) / ".dirigent") / "ROUTE.json"
    if not route_file.exists():
        return None
    try:
        raw = json.loads(route_file.read_text(encoding="utf-8"))
        RouteRecord.model_validate(raw)
        return raw
    except ValidationError as e:
        get_logger().error(f"ROUTE.json schema validation failed: {e}")
        return None


def get_next_step(repo_path: str, dirigent_dir: Optional[Path] = None) -> Optional[str]:
    """Ermittelt den nächsten auszuführenden Schritt."""
    state = load_state(repo_path, dirigent_dir=dirigent_dir)
    route = load_route(repo_path, dirigent_dir=dirigent_dir)

    if not route:
        return None

    if not state:
        return route["steps"][0]

    completed_steps = state.get("completed_steps", [])

    for step in route["steps"]:
        if step not in completed_steps:
            return step

    return None  # Alle Schritte abgeschlossen


def load_state(repo_path: str, dirigent_dir: Optional[Path] = None) -> Optional[Dict]:
    """Lädt den aktuellen State."""
    state_file = (dirigent_dir or Path(repo_path) / ".dirigent") / "STATE.json"
    if not state_file.exists():
        return None
    try:
        raw = json.loads(state_file.read_text(encoding="utf-8"))
        StateRecord.model_validate(raw)
        return raw
    except ValidationError as e:
        get_logger().error(f"STATE.json schema validation failed: {e}")
        return None


def save_state(repo_path: str, state: Dict, dirigent_dir: Optional[Path] = None):
    """Speichert den aktuellen State."""
    state_file = (dirigent_dir or Path(repo_path) / ".dirigent") / "STATE.json"
    state["updated_at"] = datetime.now().isoformat()

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def mark_step_complete(repo_path: str, step: str, dirigent_dir: Optional[Path] = None):
    """Markiert einen Schritt als abgeschlossen."""
    state = load_state(repo_path, dirigent_dir=dirigent_dir) or {
        "completed_steps": [],
        "started_at": datetime.now().isoformat(),
    }

    if "completed_steps" not in state:
        state["completed_steps"] = []

    if step not in state["completed_steps"]:
        state["completed_steps"].append(step)

    save_state(repo_path, state, dirigent_dir=dirigent_dir)
