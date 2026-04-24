"""Unit tests for final_review.

Covers the deterministic surface — Pydantic schema, internal consistency
check, parse helper, and commit-on-pass helper. The SDK call itself
(run_final_review → claude_agent_sdk) is non-deterministic and exercised
via the integration suite.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from outbid_dirigent.final_review import (
    FinalReviewComponent,
    FinalReviewErrors,
    FinalReviewReport,
    commit_passing_report,
    parse_review_report,
)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def _make_passing_report() -> FinalReviewReport:
    return FinalReviewReport(
        passed=True,
        errors_occurred=FinalReviewErrors(),
        components=[
            FinalReviewComponent(
                type="frontend",
                port=3000,
                name="Next.js app",
                is_main_entrypoint=True,
            ),
            FinalReviewComponent(
                type="backend",
                port=8000,
                name="FastAPI",
                is_main_entrypoint=False,
            ),
        ],
    )


def _make_failing_report() -> FinalReviewReport:
    return FinalReviewReport(
        passed=False,
        errors_occurred=FinalReviewErrors(
            boot_failed=True,
            other=["start.sh exited with code 127"],
        ),
        components=[],
    )


def test_passing_report_minimal_shape() -> None:
    r = _make_passing_report()
    assert r.passed is True
    assert len(r.components) == 2
    assert r.errors_occurred.boot_failed is False


def test_failing_report_minimal_shape() -> None:
    r = _make_failing_report()
    assert r.passed is False
    assert r.components == []
    assert "start.sh exited with code 127" in r.errors_occurred.other


def test_round_trip_json() -> None:
    r = _make_passing_report()
    raw = r.model_dump_json()
    parsed = FinalReviewReport.model_validate(json.loads(raw))
    assert parsed == r


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------


def test_consistency_passing_with_components_ok() -> None:
    ok, reason = _make_passing_report().is_consistent()
    assert ok is True
    assert reason == ""


def test_consistency_failing_empty_components_ok() -> None:
    ok, _reason = _make_failing_report().is_consistent()
    assert ok is True


def test_consistency_passing_without_components_fails() -> None:
    r = FinalReviewReport(
        passed=True, errors_occurred=FinalReviewErrors(), components=[]
    )
    ok, reason = r.is_consistent()
    assert ok is False
    assert "component" in reason


def test_consistency_two_main_entrypoints_fails() -> None:
    r = FinalReviewReport(
        passed=True,
        errors_occurred=FinalReviewErrors(),
        components=[
            FinalReviewComponent(type="frontend", port=3000, name="A", is_main_entrypoint=True),
            FinalReviewComponent(type="frontend", port=3001, name="B", is_main_entrypoint=True),
        ],
    )
    ok, reason = r.is_consistent()
    assert ok is False
    assert "is_main_entrypoint" in reason


def test_consistency_passing_with_errors_fails() -> None:
    r = FinalReviewReport(
        passed=True,
        errors_occurred=FinalReviewErrors(spec_requirements_unmet=["R1"]),
        components=[
            FinalReviewComponent(type="frontend", port=3000, name="A", is_main_entrypoint=True),
        ],
    )
    ok, reason = r.is_consistent()
    assert ok is False
    assert "errors_occurred" in reason


def test_consistency_failing_with_components_fails() -> None:
    r = FinalReviewReport(
        passed=False,
        errors_occurred=FinalReviewErrors(boot_failed=True),
        components=[
            FinalReviewComponent(type="frontend", port=3000, name="A", is_main_entrypoint=False),
        ],
    )
    ok, reason = r.is_consistent()
    assert ok is False


# ---------------------------------------------------------------------------
# parse_review_report
# ---------------------------------------------------------------------------


def test_parse_missing_file_returns_none(tmp_path: Path) -> None:
    assert parse_review_report(tmp_path / "nope.json") is None


def test_parse_invalid_json_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "broken.json"
    p.write_text("{ not json", encoding="utf-8")
    assert parse_review_report(p) is None


def test_parse_schema_violation_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "wrong-schema.json"
    p.write_text(json.dumps({"passed": "yes"}), encoding="utf-8")  # passed must be bool
    assert parse_review_report(p) is None


def test_parse_inconsistent_passes_validation_fails_consistency(tmp_path: Path) -> None:
    """Schema-valid but internally inconsistent → parser rejects."""
    bad = {
        "passed": True,
        "errors_occurred": {
            "boot_failed": False,
            "ports_unreachable": [],
            "spec_requirements_unmet": [],
            "credentials_missing": False,
            "other": [],
        },
        "components": [],  # passed=true with no components is inconsistent
    }
    p = tmp_path / "inconsistent.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    assert parse_review_report(p) is None


def test_parse_valid_report_round_trip(tmp_path: Path) -> None:
    r = _make_passing_report()
    p = tmp_path / "ok.json"
    p.write_text(r.model_dump_json(), encoding="utf-8")
    parsed = parse_review_report(p)
    assert parsed == r


# ---------------------------------------------------------------------------
# commit_passing_report
# ---------------------------------------------------------------------------


def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    # Need at least one commit so HEAD resolves
    (repo / ".gitkeep").write_text("")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)


def test_commit_passing_report_missing_source_returns_false(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    ok, sha = commit_passing_report(repo, run_dir, round_n=0)
    assert ok is False
    assert sha is None


def test_commit_passing_report_happy_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    report = _make_passing_report()
    (run_dir / "final-review.json").write_text(report.model_dump_json(), encoding="utf-8")

    ok, sha = commit_passing_report(repo, run_dir, round_n=1)
    assert ok is True
    assert sha is not None and len(sha) == 40

    # Verify file is at repo root and committed
    assert (repo / "final-review.json").exists()
    log = subprocess.run(
        ["git", "log", "-1", "--format=%s"], cwd=repo, capture_output=True, text=True, check=True
    )
    assert "final review passed (round 1)" in log.stdout
