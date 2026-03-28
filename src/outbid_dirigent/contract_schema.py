"""
Contract & Review schemas — typed representations for phase contracts and reviews.

Contracts define acceptance criteria before a phase starts.
Reviews evaluate changes against those criteria after execution.
Both are JSON files validated by Pydantic so Python never string-matches markdown.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


# ══════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════

class CriterionCategory(str, Enum):
    FUNCTIONAL = "functional"
    QUALITY = "quality"


class CriterionVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class Verdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    WARN = "warn"
    INFO = "info"


# ══════════════════════════════════════════
# CONTRACT SCHEMA
# ══════════════════════════════════════════

class AcceptanceCriterion(BaseModel):
    """A single measurable acceptance criterion."""
    id: str = Field(..., description="Unique ID like AC-01-01")
    description: str = Field(..., description="What must be true")
    verification: str = Field(..., description="How to verify this criterion is met")
    category: CriterionCategory = CriterionCategory.FUNCTIONAL


class ExpectedFileChange(BaseModel):
    """A file expected to change during the phase."""
    path: str
    change: str = Field(..., description="What changes in this file")


class Contract(BaseModel):
    """Phase contract — acceptance criteria agreed before execution."""
    phase_id: str
    phase_name: str
    objective: str = Field(..., description="One-sentence phase objective")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        ..., min_length=1, max_length=8,
        description="Measurable criteria (1-8)"
    )
    quality_gates: list[str] = Field(
        default_factory=lambda: [
            "All new/modified files compile without errors",
            "No regressions in existing functionality",
            "Code follows project conventions",
        ]
    )
    out_of_scope: list[str] = Field(default_factory=list)
    expected_files: list[ExpectedFileChange] = Field(default_factory=list)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> Optional["Contract"]:
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def json_template() -> str:
        return """{
  "phase_id": "01",
  "phase_name": "Phase Name",
  "objective": "One sentence: what this phase achieves",
  "acceptance_criteria": [
    {
      "id": "AC-01-01",
      "description": "Specific, measurable criterion",
      "verification": "How to verify (e.g. run command, check file exists)",
      "category": "functional"
    },
    {
      "id": "AC-01-02",
      "description": "Another criterion",
      "verification": "How to verify",
      "category": "quality"
    }
  ],
  "quality_gates": [
    "All new/modified files compile without errors",
    "No regressions in existing functionality",
    "Code follows project conventions"
  ],
  "out_of_scope": ["What this phase does NOT cover"],
  "expected_files": [
    {"path": "src/foo.py", "change": "Add new class"}
  ]
}"""

    def summary_for_prompt(self) -> str:
        """Compact summary for injection into task prompts."""
        criteria = "\n".join(
            f"  - [{c.id}] {c.description}" for c in self.acceptance_criteria
        )
        return (
            f"Phase {self.phase_id} Contract: {self.objective}\n"
            f"Acceptance Criteria:\n{criteria}"
        )


# ══════════════════════════════════════════
# REVIEW SCHEMA
# ══════════════════════════════════════════

class CriterionResult(BaseModel):
    """Evaluation of a single acceptance criterion."""
    ac_id: str = Field(..., description="References AcceptanceCriterion.id")
    verdict: CriterionVerdict
    notes: str = ""


class Finding(BaseModel):
    """A code quality finding from the review."""
    severity: FindingSeverity
    file: str
    line: int = 0
    description: str
    suggestion: str = ""


class Review(BaseModel):
    """Phase review — evaluation of changes against the contract."""
    phase_id: str
    iteration: int = 1
    verdict: Verdict
    criteria_results: list[CriterionResult] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    summary: str = ""

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARN)

    @property
    def failed_criteria(self) -> list[CriterionResult]:
        return [r for r in self.criteria_results if r.verdict == CriterionVerdict.FAIL]

    @property
    def passed_criteria(self) -> list[CriterionResult]:
        return [r for r in self.criteria_results if r.verdict == CriterionVerdict.PASS]

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> Optional["Review"]:
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def json_template() -> str:
        return """{
  "phase_id": "01",
  "iteration": 1,
  "verdict": "pass or fail",
  "criteria_results": [
    {
      "ac_id": "AC-01-01",
      "verdict": "pass",
      "notes": "Criterion met because..."
    },
    {
      "ac_id": "AC-01-02",
      "verdict": "fail",
      "notes": "Not met because..."
    }
  ],
  "findings": [
    {
      "severity": "critical",
      "file": "src/foo.py",
      "line": 42,
      "description": "Null check missing",
      "suggestion": "Add if x is None guard"
    }
  ],
  "summary": "Overall assessment"
}"""
