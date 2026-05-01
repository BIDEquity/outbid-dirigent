"""
Unit tests for the create-plan validator script.

Covers:
- Standard caps (4x4) when no route.json is present
- Large caps (5x5) when size="large"
- Quick route override (1x6) regardless of size
- Pydantic-allowed shapes still validate at the script layer

The script lives outside the importable package, so we load it via importlib
from its absolute path.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "src/outbid_dirigent/plugin/skills/create-plan/scripts/validate_schema.py"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("validate_schema", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_schema"] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _make_phase(idx: int, n_tasks: int, *, kind: str = "user-facing", last: bool = False) -> dict:
    pid = f"{idx:02d}"
    return {
        "id": pid,
        "name": f"Phase {pid}",
        "kind": kind,
        "merge_justification": "" if last else "Splitting keeps the slice reviewable.",
        "tasks": [
            {"id": f"{pid}-{j:02d}", "name": f"Ship slice {pid}-{j:02d}"}
            for j in range(1, n_tasks + 1)
        ],
    }


def _make_plan(phases: list[dict], *, size: str = "standard") -> dict:
    return {
        "title": "Test Plan",
        "summary": "test",
        "size": size,
        "phases": phases,
    }


def _write(tmp_path: Path, plan: dict, route: str | None = None) -> Path:
    plan_path = tmp_path / "PLAN.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    if route is not None:
        (tmp_path / "route.json").write_text(json.dumps({"route": route}), encoding="utf-8")
    return plan_path


# ---------------------------------------------------------------------------
# Standard route (no route.json) — caps unchanged
# ---------------------------------------------------------------------------


class TestStandardCapsRegression:
    def test_4_phases_4_tasks_passes(self, tmp_path):
        phases = [_make_phase(i, 4) for i in range(1, 5)]
        phases[-1]["merge_justification"] = ""
        plan_path = _write(tmp_path, _make_plan(phases))
        errors, _ = validator.validate(str(plan_path))
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_5_phases_rejected_at_standard(self, tmp_path):
        phases = [_make_phase(i, 1) for i in range(1, 6)]
        phases[-1]["merge_justification"] = ""
        plan_path = _write(tmp_path, _make_plan(phases))
        errors, _ = validator.validate(str(plan_path))
        assert any("max is 4" in e and "size='standard'" in e for e in errors)

    def test_large_size_allows_5_phases(self, tmp_path):
        phases = [_make_phase(i, 1) for i in range(1, 6)]
        phases[-1]["merge_justification"] = ""
        plan_path = _write(tmp_path, _make_plan(phases, size="large"))
        errors, _ = validator.validate(str(plan_path))
        assert errors == [], f"Expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# Quick route override
# ---------------------------------------------------------------------------


class TestQuickRouteCaps:
    def test_quick_one_phase_six_tasks_passes(self, tmp_path):
        phases = [_make_phase(1, 6, last=True)]
        plan_path = _write(tmp_path, _make_plan(phases), route="quick")
        errors, _ = validator.validate(str(plan_path))
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_quick_two_phases_rejected(self, tmp_path):
        phases = [_make_phase(1, 1), _make_phase(2, 1, last=True)]
        plan_path = _write(tmp_path, _make_plan(phases), route="quick")
        errors, _ = validator.validate(str(plan_path))
        assert any(
            "max is 1" in e and "route='quick'" in e for e in errors
        ), f"Expected quick-cap rejection, got: {errors}"

    def test_quick_seven_tasks_rejected(self, tmp_path):
        phases = [_make_phase(1, 7, last=True)]
        plan_path = _write(tmp_path, _make_plan(phases), route="quick")
        errors, _ = validator.validate(str(plan_path))
        # Note: Pydantic itself caps tasks at 6 — but the validator script does its
        # own counting, so it sees the raw JSON (7 tasks) and rejects with the
        # route-aware message.
        assert any(
            "max is 6" in e and "route='quick'" in e for e in errors
        ), f"Expected per-phase task-cap rejection, got: {errors}"

    def test_quick_size_large_does_not_lift_caps(self, tmp_path):
        """Route override wins: quick + size=large still capped at 1x6."""
        phases = [_make_phase(1, 1), _make_phase(2, 1, last=True)]
        plan_path = _write(tmp_path, _make_plan(phases, size="large"), route="quick")
        errors, _ = validator.validate(str(plan_path))
        assert any(
            "max is 1" in e and "route='quick'" in e for e in errors
        ), f"Expected quick caps to win over size=large, got: {errors}"

    def test_non_quick_route_uses_size_caps(self, tmp_path):
        """A hybrid-route plan with 4 phases × 4 tasks still passes under standard caps."""
        phases = [_make_phase(i, 4) for i in range(1, 5)]
        phases[-1]["merge_justification"] = ""
        plan_path = _write(tmp_path, _make_plan(phases), route="hybrid")
        errors, _ = validator.validate(str(plan_path))
        assert errors == [], f"Expected no errors, got: {errors}"

    def test_corrupt_route_json_falls_back_to_size(self, tmp_path):
        """Garbage in route.json must not crash the validator; fall back to size caps."""
        phases = [_make_phase(i, 4) for i in range(1, 5)]
        phases[-1]["merge_justification"] = ""
        plan_path = _write(tmp_path, _make_plan(phases))
        (tmp_path / "route.json").write_text("not json at all", encoding="utf-8")
        errors, _ = validator.validate(str(plan_path))
        assert errors == [], f"Expected fallback to standard caps, got: {errors}"
