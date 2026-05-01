"""
Plan schema — typed representation of PLAN.json.

Uses pydantic for validation, serialization, and deserialization.
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PhaseKind(str, Enum):
    """How a phase relates to the user.

    Drives layer quotas in contracts and plan-level validation (max 1
    infrastructure, final phase ≠ infrastructure, etc).
    """

    USER_FACING = "user-facing"  # Delivers UI surface or observable behavior change
    INTEGRATION = "integration"  # Subsystem a later phase will expose to users
    INFRASTRUCTURE = "infrastructure"  # Scaffolding, migrations, tooling — no consumer in-run


class Task(BaseModel):
    """A single executable task within a phase."""

    id: str
    name: str
    description: str = ""
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    model: Literal["", "haiku", "sonnet", "opus"] = ""
    effort: Literal["", "low", "medium", "high", "xhigh", "max"] = ""
    test_level: Literal["", "L1", "L2"] = ""
    convention_skills: list[str] = Field(
        default_factory=list
    )  # e.g. ["ruby-code-writing", "form-builder"]
    relevant_req_ids: list[str] = Field(
        default_factory=list
    )  # e.g. ["R3", "R7"] from SPEC.compact.json


class Phase(BaseModel):
    """A group of related tasks executed sequentially."""

    id: str
    name: str
    kind: PhaseKind = Field(
        default=PhaseKind.USER_FACING,
        description="user-facing | integration | infrastructure — drives contract layer quotas",
    )
    description: str = ""
    merge_justification: str = Field(
        default="",
        description="One sentence: why this phase can't be merged with the next. Empty only if this is the last phase.",
    )
    tasks: list[Task] = Field(default_factory=list, max_length=6)

    def model_post_init(self, __context):
        # Normalize: accept both "id" and "phase" field names
        if not self.id and hasattr(self, "phase"):
            self.id = str(getattr(self, "phase"))


class Plan(BaseModel):
    """The full execution plan for a dirigent run."""

    title: str = "Untitled"
    summary: str = ""
    size: Literal["standard", "large"] = Field(
        default="standard",
        description="'large' raises validator caps from 4 phases × 4 tasks to 5 × 5. Use only when the feature genuinely cannot fit 4×4 — summary must justify.",
    )
    phases: list[Phase] = Field(default_factory=list, max_length=5)
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
            # Normalize phase/task fields from common LLM output variations
            for p in raw.get("phases", []):
                if "phase" in p and "id" not in p:
                    p["id"] = str(p.pop("phase"))
                elif "id" in p:
                    p["id"] = str(p["id"])
                # Pre-plan-tuning plans have no phase kind — default to user-facing
                # (tightest downstream contract quotas; loudest if misclassified)
                if "kind" not in p:
                    p["kind"] = "user-facing"
                for t in p.get("tasks", []):
                    # title → name
                    if "title" in t and "name" not in t:
                        t["name"] = t.pop("title")
                    # files → files_to_modify (conservative default)
                    if "files" in t and "files_to_modify" not in t and "files_to_create" not in t:
                        t["files_to_modify"] = t.pop("files")
            return cls.model_validate(raw)
        except json.JSONDecodeError as e:
            logger.error("PLAN.json is not valid JSON: %s", e)
            return None
        except Exception as e:
            logger.error("PLAN.json validation failed: %s", e)
            return None

    @staticmethod
    def json_template() -> str:
        """JSON template string for the plan creation prompt."""
        return """{
  "title": "Feature-Titel",
  "summary": "Kurze Beschreibung was implementiert wird",
  "size": "standard",
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
      "kind": "user-facing|integration|infrastructure",
      "description": "Was in dieser Phase passiert",
      "merge_justification": "Ein Satz: warum diese Phase nicht mit der naechsten gemerged werden kann. Leer nur bei der letzten Phase.",
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
          "test_level": "L1|L2| (welches Test-Level nach diesem Task laufen soll, leer wenn kein Test nötig)",
          "convention_skills": ["skill-name-1", "skill-name-2 (aus .opencode/skills/, leer wenn keine)"],
          "relevant_req_ids": ["R3", "R7 (IDs aus SPEC.compact.json — welche Requirements dieser Task adressiert)"]
        }
      ]
    }
  ],
  "estimated_complexity": "low|medium|high",
  "risks": ["Liste von potentiellen Risiken"]
}"""
