"""Unit tests for spec_validator.

Covers the deterministic surface only — Pydantic schema, error path, and
the file-write side effect. The LLM call itself (validate_spec → SDK) is
non-deterministic and tested via the integration suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from outbid_dirigent.spec_validator import (
    SpecGap,
    SpecValidation,
    SpecValidationError,
    _gather_repo_context,
    _save_validation,
)


def test_spec_validation_minimal_ok() -> None:
    v = SpecValidation(
        spec_ok=True, spec_ok_rationale="", rejection_reason="", spec_gaps=[]
    )
    assert v.spec_ok is True
    assert v.spec_gaps == []


def test_spec_validation_with_gaps() -> None:
    v = SpecValidation(
        spec_ok=True,
        spec_ok_rationale="",
        rejection_reason="",
        spec_gaps=[
            SpecGap(
                area="navigation",
                severity="warn",
                summary="No nav surface mentioned",
                rationale="Greenfield app needs an entry point",
                suggested_addition="Add a `/dashboard` route as the authenticated landing.",
            )
        ],
    )
    assert len(v.spec_gaps) == 1
    assert v.spec_gaps[0].area == "navigation"


def test_spec_validation_rejected() -> None:
    v = SpecValidation(
        spec_ok=False,
        spec_ok_rationale="Spec is one sentence with no testable requirements.",
        rejection_reason="insufficient",
        spec_gaps=[],
    )
    assert v.spec_ok is False
    assert v.rejection_reason == "insufficient"


def test_spec_validation_error_carries_validation() -> None:
    v = SpecValidation(
        spec_ok=False,
        spec_ok_rationale="Content policy violation.",
        rejection_reason="nsfw",
        spec_gaps=[],
    )
    err = SpecValidationError(v)
    assert err.validation is v
    assert "Content policy violation." in str(err)


def test_spec_validation_round_trip() -> None:
    """JSON serialization is stable so the persisted SPEC.validation.json
    can be re-loaded by the user / portal without surprises."""
    v = SpecValidation(
        spec_ok=True,
        spec_ok_rationale="",
        rejection_reason="",
        spec_gaps=[
            SpecGap(
                area="authentication",
                severity="info",
                summary="No auth approach mentioned",
                rationale="Greenfield route default would pick PocketBase or Supabase.",
                suggested_addition="Add: 'Auth: email+password via PocketBase.'",
            )
        ],
    )
    raw = v.model_dump_json()
    parsed = SpecValidation.model_validate(json.loads(raw))
    assert parsed == v


def test_save_validation_writes_file(tmp_path: Path) -> None:
    v = SpecValidation(
        spec_ok=True, spec_ok_rationale="", rejection_reason="", spec_gaps=[]
    )
    _save_validation(tmp_path, v)
    out = tmp_path / "SPEC.validation.json"
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["spec_ok"] is True


def test_gather_repo_context_returns_empty_when_no_files(tmp_path: Path) -> None:
    assert _gather_repo_context(tmp_path) == ""


def test_gather_repo_context_picks_up_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# My Project\n", encoding="utf-8")
    ctx = _gather_repo_context(tmp_path)
    assert "README" in ctx
    assert "# My Project" in ctx


def test_gather_repo_context_caps_at_5000_bytes(tmp_path: Path) -> None:
    big = "x" * 10_000
    (tmp_path / "ARCHITECTURE.md").write_text(big, encoding="utf-8")
    ctx = _gather_repo_context(tmp_path)
    # 5000 bytes of x's plus the heading and label
    assert ctx.count("x") == 5000


@pytest.mark.parametrize(
    "reason",
    ["", "insufficient", "code-mismatch", "nsfw", "gambling", "illegal", "policy-violation", "other"],
)
def test_rejection_reason_enum_values(reason: str) -> None:
    v = SpecValidation(
        spec_ok=False if reason else True,
        spec_ok_rationale="" if not reason else "test",
        rejection_reason=reason,
        spec_gaps=[],
    )
    assert v.rejection_reason == reason
