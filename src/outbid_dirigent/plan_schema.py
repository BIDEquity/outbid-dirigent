"""
Plan schema — typed representation of PLAN.json.

Uses pydantic for validation, serialization, and deserialization.
"""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    """A single executable task within a phase."""
    id: str
    name: str
    description: str = ""
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    model: str = ""
    effort: str = ""
    test_level: str = ""  # "", "L1", "L2"


class Phase(BaseModel):
    """A group of related tasks executed sequentially."""
    id: str
    name: str
    description: str = ""
    tasks: list[Task] = Field(default_factory=list)

    def model_post_init(self, __context):
        # Normalize: accept both "id" and "phase" field names
        if not self.id and hasattr(self, "phase"):
            self.id = str(getattr(self, "phase"))


class Plan(BaseModel):
    """The full execution plan for a dirigent run."""
    title: str = "Untitled"
    summary: str = ""
    phases: list[Phase] = Field(default_factory=list)
    estimated_complexity: str = "medium"
    risks: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)

    @property
    def total_tasks(self) -> int:
        return sum(len(p.tasks) for p in self.phases)

    @property
    def all_tasks(self) -> list[tuple[Task, Phase]]:
        """Flat list of (task, phase) in execution order."""
        return [(t, p) for p in self.phases for t in p.tasks]

    def task_position(self, task_id: str) -> Optional[dict]:
        """Position info for a task: index, total, phase, prev/next."""
        tasks = self.all_tasks
        idx = next((i for i, (t, _) in enumerate(tasks) if t.id == task_id), None)
        if idx is None:
            return None

        t, p = tasks[idx]
        info = {
            "index": idx + 1,
            "total": len(tasks),
            "phase_id": p.id,
            "phase_name": p.name,
            "total_phases": len(self.phases),
        }
        if idx > 0:
            prev_t, _ = tasks[idx - 1]
            info["prev_id"] = prev_t.id
            info["prev_name"] = prev_t.name
        if idx < len(tasks) - 1:
            next_t, _ = tasks[idx + 1]
            info["next_id"] = next_t.id
            info["next_name"] = next_t.name
        return info

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> Optional["Plan"]:
        """Load from PLAN.json. Returns None if missing or invalid."""
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            # Normalize phase id field
            for p in raw.get("phases", []):
                if "phase" in p and "id" not in p:
                    p["id"] = str(p.pop("phase"))
                elif "id" in p:
                    p["id"] = str(p["id"])
            return cls.model_validate(raw)
        except Exception:
            return None

    @staticmethod
    def json_template() -> str:
        """JSON template string for the plan creation prompt."""
        return """{
  "title": "Feature-Titel",
  "summary": "Kurze Beschreibung was implementiert wird",
  "assumptions": [
    "Annahmen die du über die Codebase/das Feature machst",
    "z.B. 'Tests laufen mit pytest', 'API ist REST-basiert'"
  ],
  "out_of_scope": [
    "Was NICHT Teil dieses Plans ist",
    "z.B. 'Deployment/CI-Pipeline', 'Performance-Optimierung'"
  ],
  "phases": [
    {
      "id": "01",
      "name": "Phase-Name",
      "description": "Was in dieser Phase passiert",
      "tasks": [
        {
          "id": "01-01",
          "name": "Task-Name",
          "description": "Detaillierte Beschreibung was zu tun ist",
          "files_to_create": ["liste/von/neuen/dateien.ext"],
          "files_to_modify": ["liste/von/existierenden/dateien.ext"],
          "depends_on": [],
          "model": "sonnet|haiku|opus (welches Modell für diesen Task am besten ist)",
          "effort": "low|medium|high (wie viel Denkaufwand nötig ist)",
          "test_level": "L1|L2| (welches Test-Level nach diesem Task laufen soll, leer wenn kein Test nötig)"
        }
      ]
    }
  ],
  "estimated_complexity": "low|medium|high",
  "risks": ["Liste von potentiellen Risiken"]
}"""
