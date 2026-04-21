"""Unit tests for router.py — estimate_tasks, state CRUD, get_next_step, route save/load."""

import json
from pathlib import Path
from typing import cast

import pytest

from outbid_dirigent.logger import DirigentLogger
from outbid_dirigent.router import (
    Router,
    RouteType,
    StepType,
    load_state,
    save_state,
    mark_step_complete,
    get_next_step,
    load_route,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_router(tmp_path: Path) -> Router:
    # Silent no-op logger. Cast to DirigentLogger so Pyright is satisfied
    # without needing to instantiate the full logger (which writes to disk).
    silent_logger = cast(
        DirigentLogger,
        type(
            "L", (), {k: (lambda *a, **kw: None) for k in ["debug", "info", "warning", "error"]}
        )(),
    )
    router = Router.__new__(Router)
    router.repo_path = tmp_path
    router.logger = silent_logger
    return router


def _minimal_route_json(steps: list[str]) -> dict:
    return {
        "route": "greenfield",
        "reason": "test",
        "steps": steps,
        "step_details": [
            {"type": s, "name": s, "description": "", "required": True} for s in steps
        ],
        "estimated_tasks": 4,
        "oracle_needed": False,
        "repo_context_needed": False,
        "created_at": "2024-01-01T00:00:00",
    }


# ---------------------------------------------------------------------------
# TestEstimateTasks
# ---------------------------------------------------------------------------


class TestEstimateTasks:
    def test_small(self, tmp_path):
        assert make_router(tmp_path)._estimate_tasks("small") == 4

    def test_medium(self, tmp_path):
        assert make_router(tmp_path)._estimate_tasks("medium") == 8

    def test_large(self, tmp_path):
        assert make_router(tmp_path)._estimate_tasks("large") == 12

    def test_unknown_defaults_to_6(self, tmp_path):
        assert make_router(tmp_path)._estimate_tasks("xlarge") == 6

    def test_empty_string_defaults_to_6(self, tmp_path):
        assert make_router(tmp_path)._estimate_tasks("") == 6


# ---------------------------------------------------------------------------
# TestBuildRoute
# ---------------------------------------------------------------------------


class TestBuildRoute:
    def test_greenfield_dict_route_type(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "fresh project",
            "estimated_scope": "small",
            "file_count": 15,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.route_type == RouteType.GREENFIELD

    def test_greenfield_tasks_from_scope(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "small",
            "file_count": 15,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.estimated_tasks == 4

    def test_greenfield_oracle_not_needed(self, tmp_path):
        """Not legacy, commits <= 200 → oracle_needed=False."""
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "small",
            "file_count": 15,
            "commit_count": 50,
        }
        route = router.determine_route(analysis)
        assert route.oracle_needed is False

    def test_greenfield_repo_context_needed_when_many_files(self, tmp_path):
        """file_count > 10 → repo_context_needed=True."""
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "small",
            "file_count": 15,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.repo_context_needed is True

    def test_repo_context_not_needed_when_few_files(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "small",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.repo_context_needed is False

    def test_legacy_oracle_needed(self, tmp_path):
        """Legacy route always sets oracle_needed=True."""
        router = make_router(tmp_path)
        analysis = {
            "route": "legacy",
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.oracle_needed is True

    def test_oracle_needed_when_high_commit_count(self, tmp_path):
        """commit_count > 200 sets oracle_needed even for non-legacy routes."""
        router = make_router(tmp_path)
        analysis = {
            "route": "hybrid",
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 201,
        }
        route = router.determine_route(analysis)
        assert route.oracle_needed is True

    @pytest.mark.parametrize(
        "route_str,route_type",
        [
            ("quick", RouteType.QUICK),
            ("legacy", RouteType.LEGACY),
            ("hybrid", RouteType.HYBRID),
            ("testability", RouteType.TESTABILITY),
            ("tracking", RouteType.TRACKING),
        ],
    )
    def test_non_greenfield_routes_start_with_harness_install(
        self, tmp_path, route_str, route_type
    ):
        router = make_router(tmp_path)
        analysis = {
            "route": route_str,
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.steps[0].step_type == StepType.HARNESS_INSTALL

    @pytest.mark.parametrize(
        "route_str",
        ["legacy", "hybrid", "testability", "tracking"],
    )
    def test_non_greenfield_routes_run_init_after_harness(self, tmp_path, route_str):
        router = make_router(tmp_path)
        analysis = {
            "route": route_str,
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.steps[1].step_type == StepType.INIT

    def test_greenfield_starts_with_scaffold(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.steps[0].step_type == StepType.GREENFIELD_SCAFFOLD

    def test_greenfield_runs_harness_install_after_scaffold(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.steps[1].step_type == StepType.HARNESS_INSTALL

    @pytest.mark.parametrize(
        "route_str",
        [
            "greenfield",
            "legacy",
            "hybrid",
            "testability",
            "tracking",
        ],
    )
    def test_all_routes_end_with_ship(self, tmp_path, route_str):
        router = make_router(tmp_path)
        analysis = {
            "route": route_str,
            "route_reason": "",
            "estimated_scope": "medium",
            "file_count": 5,
            "commit_count": 10,
        }
        route = router.determine_route(analysis)
        assert route.steps[-1].step_type == StepType.SHIP


# ---------------------------------------------------------------------------
# TestStateCRUD
# ---------------------------------------------------------------------------


class TestStateCRUD:
    def test_load_state_returns_none_when_missing(self, tmp_path):
        # .dirigent dir exists (created by _init_logger), but no STATE.json
        assert load_state(str(tmp_path)) is None

    def test_save_and_load_roundtrip(self, tmp_path):
        state = {"completed_steps": ["init"], "started_at": "2024-01-01T00:00:00"}
        save_state(str(tmp_path), state)
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded["completed_steps"] == ["init"]

    def test_save_adds_updated_at(self, tmp_path):
        state = {"completed_steps": [], "started_at": "2024-01-01T00:00:00"}
        save_state(str(tmp_path), state)
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded["updated_at"] != ""

    def test_mark_step_complete_creates_state_if_missing(self, tmp_path):
        mark_step_complete(str(tmp_path), "init")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert "init" in loaded["completed_steps"]

    def test_mark_step_complete_is_idempotent(self, tmp_path):
        mark_step_complete(str(tmp_path), "init")
        mark_step_complete(str(tmp_path), "init")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded["completed_steps"].count("init") == 1

    def test_mark_step_complete_appends_multiple(self, tmp_path):
        mark_step_complete(str(tmp_path), "init")
        mark_step_complete(str(tmp_path), "planning")
        loaded = load_state(str(tmp_path))
        assert loaded is not None
        assert loaded["completed_steps"] == ["init", "planning"]

    def test_load_state_rejects_invalid_schema(self, tmp_path):
        d = tmp_path / ".dirigent"
        (d / "STATE.json").write_text('{"bad_field": 42}', encoding="utf-8")
        assert load_state(str(tmp_path)) is None

    def test_load_state_rejects_bad_json(self, tmp_path):
        d = tmp_path / ".dirigent"
        (d / "STATE.json").write_text("not json at all", encoding="utf-8")
        with pytest.raises(Exception):
            load_state(str(tmp_path))


# ---------------------------------------------------------------------------
# TestGetNextStep
# ---------------------------------------------------------------------------


class TestGetNextStep:
    def _write_route(self, tmp_path: Path, steps: list[str]):
        d = tmp_path / ".dirigent"
        (d / "ROUTE.json").write_text(json.dumps(_minimal_route_json(steps)), encoding="utf-8")

    def test_returns_first_step_when_no_state(self, tmp_path):
        self._write_route(tmp_path, ["init", "planning", "ship"])
        assert get_next_step(str(tmp_path)) == "init"

    def test_returns_next_incomplete_step(self, tmp_path):
        self._write_route(tmp_path, ["init", "planning", "ship"])
        mark_step_complete(str(tmp_path), "init")
        assert get_next_step(str(tmp_path)) == "planning"

    def test_returns_none_when_all_complete(self, tmp_path):
        self._write_route(tmp_path, ["init", "planning", "ship"])
        for step in ["init", "planning", "ship"]:
            mark_step_complete(str(tmp_path), step)
        assert get_next_step(str(tmp_path)) is None

    def test_returns_none_when_no_route_file(self, tmp_path):
        assert get_next_step(str(tmp_path)) is None


# ---------------------------------------------------------------------------
# TestRouteLoadSave
# ---------------------------------------------------------------------------


class TestRouteLoadSave:
    def test_load_route_returns_none_when_missing(self, tmp_path):
        assert load_route(str(tmp_path)) is None

    def test_save_and_load_roundtrip(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "greenfield",
            "route_reason": "new project",
            "estimated_scope": "medium",
            "file_count": 20,
            "commit_count": 5,
        }
        route = router.determine_route(analysis)
        router.save_route(route)

        loaded = load_route(str(tmp_path))
        assert loaded is not None
        assert loaded["route"] == "greenfield"
        assert loaded["estimated_tasks"] == 8
        assert loaded["oracle_needed"] is False
        assert loaded["repo_context_needed"] is True
        assert "greenfield_scaffold" in loaded["steps"]
        assert "ship" in loaded["steps"]

    def test_save_route_writes_created_at(self, tmp_path):
        router = make_router(tmp_path)
        analysis = {
            "route": "hybrid",
            "route_reason": "",
            "estimated_scope": "small",
            "file_count": 3,
            "commit_count": 0,
        }
        route = router.determine_route(analysis)
        router.save_route(route)
        loaded = load_route(str(tmp_path))
        assert loaded is not None
        assert loaded["created_at"] != ""
