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

from loguru import logger
from pydantic import BaseModel, Field

# PhaseKind is defined upstream in plan_schema (phases are planned before contracts are drafted).
# Re-exported here so existing `from outbid_dirigent.contract_schema import PhaseKind` keeps working.
from outbid_dirigent.plan_schema import PhaseKind  # noqa: F401


# ══════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════


class CriterionLayer(str, Enum):
    STRUCTURAL = "structural"  # Compile, lint, typecheck, subsystem liveness
    UNIT = "unit"  # Fast isolated tests for new logic in this phase
    USER_JOURNEY = "user-journey"  # End-to-end: a user (or calling subsystem) observes X
    EDGE_CASE = "edge-case"  # User or subsystem hits a bad path; graceful response


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
    verification: str = Field(..., description="Executable command to verify (Run: ...)")
    layer: CriterionLayer = CriterionLayer.USER_JOURNEY


class ExpectedFileChange(BaseModel):
    """A file expected to change during the phase."""

    path: str
    change: str = Field(..., description="What changes in this file")


class Contract(BaseModel):
    """Phase contract — acceptance criteria agreed before execution."""

    phase_id: str
    phase_name: str
    phase_kind: PhaseKind = Field(
        default=PhaseKind.USER_FACING,
        description="user-facing | integration | infrastructure — drives layer quotas",
    )
    objective: str = Field(..., description="Starts with a verb the user performs")
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        ..., min_length=1, max_length=8, description="Measurable criteria (1-8)"
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
            raw = json.loads(path.read_text(encoding="utf-8"))
            # Backward compat: map legacy fields to current schema
            for criterion in raw.get("acceptance_criteria", []):
                # Pre-2025 'category' field → 'layer'
                if "category" in criterion and "layer" not in criterion:
                    category = criterion.pop("category")
                    criterion["layer"] = {
                        "functional": "user-journey",
                        "quality": "structural",
                    }.get(category, "user-journey")
                # Pre-UX-reframe layer names → current names
                legacy_layer = criterion.get("layer")
                if legacy_layer == "behavioral":
                    criterion["layer"] = "user-journey"
                elif legacy_layer == "boundary":
                    criterion["layer"] = "edge-case"
            # Pre-UX-reframe contracts have no phase_kind — default to user-facing
            if "phase_kind" not in raw:
                raw["phase_kind"] = "user-facing"
            return cls.model_validate(raw)
        except Exception:
            return None

    @staticmethod
    def json_template() -> str:
        return """{
  "phase_id": "04",
  "phase_name": "User Management",
  "phase_kind": "user-facing",
  "objective": "An admin can add, edit, and disable users and see the results immediately on screen",
  "acceptance_criteria": [
    {
      "id": "AC-04-01",
      "description": "Project compiles and the admin area is reachable",
      "verification": "Run: npm run build && (npm run dev &) && sleep 4 && curl -sf http://localhost:3000/admin",
      "layer": "structural"
    },
    {
      "id": "AC-04-02",
      "description": "The user-form validator rejects empty email, invalid email format, and emails over 254 chars; accepts RFC-compliant emails",
      "verification": "Run: pnpm test -- src/users/validators.test.ts --run",
      "layer": "unit"
    },
    {
      "id": "AC-04-03",
      "description": "After logging in as admin and opening User Management, the admin sees existing users listed with email and role",
      "verification": "Run: npx playwright test --grep 'admin sees user list' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-04",
      "description": "The admin clicks 'Add User', fills email + role, submits, and sees the new row appear in the table without a page reload",
      "verification": "Run: npx playwright test --grep 'admin adds user inline' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-05",
      "description": "The admin changes a user's role and saves; the row updates in place and persists across reload",
      "verification": "Run: npx playwright test --grep 'admin edits role persists' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-06",
      "description": "When the admin submits a duplicate email, they see 'This email is already registered' next to the email field and the form stays open",
      "verification": "Run: npx playwright test --grep 'duplicate email inline error' --reporter=line",
      "layer": "edge-case"
    }
  ],
  "quality_gates": [
    "All new/modified files compile without errors",
    "No regressions in existing functionality",
    "Code follows project conventions"
  ],
  "out_of_scope": ["Password reset flow", "Bulk user import"],
  "expected_files": [
    {"path": "src/users/validators.ts", "change": "Email and role validators"},
    {"path": "src/users/validators.test.ts", "change": "Unit tests for validators"},
    {"path": "src/app/admin/users/page.tsx", "change": "User management screen"},
    {"path": "tests/e2e/admin-users.spec.ts", "change": "Playwright specs for user-journey criteria"}
  ]
}"""

    def summary_for_prompt(self) -> str:
        """Compact summary for injection into task prompts — includes verification commands."""
        criteria = "\n".join(
            f"  - [{c.id}] ({c.layer.value}) {c.description}\n    Verify: {c.verification}"
            for c in self.acceptance_criteria
        )
        return f"Phase {self.phase_id} Contract: {self.objective}\nAcceptance Criteria:\n{criteria}"


# ══════════════════════════════════════════
# REVIEW SCHEMA
# ══════════════════════════════════════════


class VerificationEvidence(BaseModel):
    """Proof that a verification command was actually executed."""

    command: str = Field(..., description="The command that was run")
    exit_code: int = Field(..., description="Exit code of the command")
    stdout_snippet: str = Field("", description="First 500 chars of stdout")
    stderr_snippet: str = Field("", description="First 500 chars of stderr")


class CriterionResult(BaseModel):
    """Evaluation of a single acceptance criterion."""

    ac_id: str = Field(..., description="References AcceptanceCriterion.id")
    verdict: CriterionVerdict
    notes: str = ""
    evidence: list[VerificationEvidence] = Field(
        default_factory=list,
        description="Commands run to verify this criterion. Required for functional criteria.",
    )
    verification_tier: str = ""  # InfraTier value used to verify this criterion


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
    confidence: str = "static"  # e2e | integration | unit | mocked | static | none
    infra_tier: str = "7_none"  # InfraTier value active during execution
    tests_run: int = 0
    tests_skipped_infra: int = 0
    caveat: str = ""  # human-readable explanation of what wasn't verified
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

    @property
    def criteria_without_evidence(self) -> list[CriterionResult]:
        """Criteria marked as pass but with no verification evidence."""
        return [
            r
            for r in self.criteria_results
            if r.verdict == CriterionVerdict.PASS and not r.evidence
        ]

    @property
    def warned_criteria(self) -> list[CriterionResult]:
        """Criteria that could not be verified due to infrastructure constraints."""
        return [r for r in self.criteria_results if r.verdict == CriterionVerdict.WARN]

    @property
    def infra_constrained_only(self) -> bool:
        """True when all failures are infra-constrained (WARN) with no real code failures."""
        return not self.failed_criteria and self.critical_count == 0 and bool(self.warned_criteria)

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @classmethod
    def _normalize_raw(cls, raw: dict) -> dict:
        """Aggressively normalize a raw review dict for Pydantic compatibility."""
        # Normalize top-level verdict
        if "verdict" in raw and isinstance(raw["verdict"], str):
            raw["verdict"] = raw["verdict"].strip().lower()
            if raw["verdict"] not in ("pass", "fail"):
                raw["verdict"] = "fail"  # unknown verdict → fail

        # Backward compat: old field names
        if "results" in raw and "criteria_results" not in raw:
            old_results = raw.pop("results")
            raw["criteria_results"] = [
                {
                    "ac_id": r.get("id", ""),
                    "verdict": r.get("status", "fail").lower(),
                    "notes": r.get("actual") or r.get("notes") or "",
                }
                for r in old_results
            ]
        if "issues" in raw and "findings" not in raw:
            _sev_map = {"low": "info", "medium": "warn", "high": "critical"}
            raw["findings"] = [
                {
                    "severity": _sev_map.get(i.get("severity", "info"), i.get("severity", "info")),
                    "file": i.get("criterion", ""),
                    "line": 0,
                    "description": i.get("description", ""),
                    "suggestion": i.get("recommendation", ""),
                }
                for i in raw.pop("issues")
            ]

        # Normalize criterion verdicts
        valid_cr_verdicts = {"pass", "fail", "warn"}
        for cr in raw.get("criteria_results", []):
            if "verdict" in cr and isinstance(cr["verdict"], str):
                cr["verdict"] = cr["verdict"].strip().lower()
                if cr["verdict"] not in valid_cr_verdicts:
                    cr["verdict"] = "fail"
            # Ensure required fields exist
            if "ac_id" not in cr:
                cr["ac_id"] = "UNKNOWN"
            if "verdict" not in cr:
                cr["verdict"] = "fail"

        # Normalize finding severities
        valid_severities = {"critical", "warn", "info"}
        for f in raw.get("findings", []):
            if "severity" in f and isinstance(f["severity"], str):
                f["severity"] = f["severity"].strip().lower()
                if f["severity"] not in valid_severities:
                    f["severity"] = "warn"
            # Ensure required fields exist
            if "file" not in f:
                f["file"] = "unknown"
            if "description" not in f:
                f["description"] = ""

        # Strip unknown top-level fields that Pydantic might reject
        known_fields = {
            "phase_id",
            "iteration",
            "verdict",
            "confidence",
            "infra_tier",
            "tests_run",
            "tests_skipped_infra",
            "caveat",
            "criteria_results",
            "findings",
            "summary",
        }
        unknown = set(raw.keys()) - known_fields
        for key in unknown:
            raw.pop(key)

        # Ensure phase_id is a string
        if "phase_id" in raw:
            raw["phase_id"] = str(raw["phase_id"])

        return raw

    @classmethod
    def load(cls, path: Path) -> Optional["Review"]:
        if not path.exists():
            return None
        try:
            content = path.read_text(encoding="utf-8")
            if not content.strip():
                logger.warning(f"Review file is empty: {path}")
                return None
            raw = json.loads(content)
            raw = cls._normalize_raw(raw)
            return cls.model_validate(raw)
        except Exception as e:
            logger.error(f"Review.load() failed for {path}: {e}")
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
