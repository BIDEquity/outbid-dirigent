"""
Unit tests for plan_schema.py — Plan, Phase, Task models.

Covers: properties, save/load roundtrip, backward compatibility normalization.
"""

import json


from outbid_dirigent.plan_schema import Phase, Plan, Task


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _simple_plan() -> Plan:
    return Plan(
        title="Test Feature",
        phases=[
            Phase(
                id="01",
                name="Core",
                tasks=[
                    Task(id="01-01", name="Setup DB"),
                    Task(id="01-02", name="Add API"),
                ],
            ),
            Phase(
                id="02",
                name="Ship",
                tasks=[
                    Task(id="02-01", name="Create PR"),
                ],
            ),
        ],
    )


# ---------------------------------------------------------------------------
# TestPlanProperties
# ---------------------------------------------------------------------------


class TestPlanProperties:
    def test_total_tasks(self):
        plan = _simple_plan()
        assert plan.total_tasks == 3

    def test_total_tasks_empty(self):
        plan = Plan()
        assert plan.total_tasks == 0

    def test_all_tasks_flat_list(self):
        plan = _simple_plan()
        result = plan.all_tasks
        assert len(result) == 3
        # Each entry is a (Task, Phase) tuple
        task_ids = [t.id for t, _ in result]
        assert task_ids == ["01-01", "01-02", "02-01"]

    def test_all_tasks_correct_phases(self):
        plan = _simple_plan()
        result = plan.all_tasks
        phase_ids = [p.id for _, p in result]
        assert phase_ids == ["01", "01", "02"]


# ---------------------------------------------------------------------------
# TestTaskPosition
# ---------------------------------------------------------------------------


class TestTaskPosition:
    def test_first_task_no_prev_has_next(self):
        plan = _simple_plan()
        pos = plan.task_position("01-01")
        assert pos is not None
        assert pos["index"] == 1
        assert pos["total"] == 3
        assert pos["phase_id"] == "01"
        assert pos["phase_name"] == "Core"
        assert pos["total_phases"] == 2
        assert "prev_id" not in pos
        assert "prev_name" not in pos
        assert pos["next_id"] == "01-02"
        assert pos["next_name"] == "Add API"

    def test_middle_task_has_prev_and_next(self):
        plan = _simple_plan()
        pos = plan.task_position("01-02")
        assert pos is not None
        assert pos["index"] == 2
        assert pos["prev_id"] == "01-01"
        assert pos["prev_name"] == "Setup DB"
        assert pos["next_id"] == "02-01"
        assert pos["next_name"] == "Create PR"

    def test_last_task_has_prev_no_next(self):
        plan = _simple_plan()
        pos = plan.task_position("02-01")
        assert pos is not None
        assert pos["index"] == 3
        assert pos["total"] == 3
        assert pos["phase_id"] == "02"
        assert pos["phase_name"] == "Ship"
        assert pos["prev_id"] == "01-02"
        assert pos["prev_name"] == "Add API"
        assert "next_id" not in pos
        assert "next_name" not in pos

    def test_nonexistent_task_returns_none(self):
        plan = _simple_plan()
        assert plan.task_position("does-not-exist") is None


# ---------------------------------------------------------------------------
# TestPlanSaveLoad
# ---------------------------------------------------------------------------


class TestPlanSaveLoad:
    def test_roundtrip(self, tmp_path):
        plan = _simple_plan()
        dest = tmp_path / "PLAN.json"
        plan.save(dest)
        loaded = Plan.load(dest)
        assert loaded is not None
        assert loaded.title == "Test Feature"
        assert loaded.total_tasks == 3
        assert loaded.phases[0].id == "01"
        assert loaded.phases[1].id == "02"

    def test_missing_file_returns_none(self, tmp_path):
        result = Plan.load(tmp_path / "nonexistent.json")
        assert result is None

    def test_invalid_json_returns_none(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not valid json }", encoding="utf-8")
        assert Plan.load(bad) is None

    def test_backward_compat_phase_key_renamed_to_id(self, tmp_path):
        """Old format uses 'phase' instead of 'id' for phase identifier."""
        raw = {
            "title": "Legacy Plan",
            "phases": [
                {
                    "phase": "01",
                    "name": "Old Phase",
                    "tasks": [],
                }
            ],
        }
        dest = tmp_path / "old.json"
        dest.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Plan.load(dest)
        assert loaded is not None
        assert loaded.phases[0].id == "01"
        assert loaded.phases[0].name == "Old Phase"

    def test_numeric_phase_id_stringified(self, tmp_path):
        """Numeric phase ids (e.g. 1) must be stringified to '1'."""
        raw = {
            "title": "Numeric IDs",
            "phases": [
                {
                    "id": 1,
                    "name": "First Phase",
                    "tasks": [],
                },
                {
                    "id": 2,
                    "name": "Second Phase",
                    "tasks": [],
                },
            ],
        }
        dest = tmp_path / "numeric.json"
        dest.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Plan.load(dest)
        assert loaded is not None
        assert loaded.phases[0].id == "1"
        assert loaded.phases[1].id == "2"
