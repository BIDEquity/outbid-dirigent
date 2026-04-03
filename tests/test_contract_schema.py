"""
Unit tests for contract_schema.py (Contract, Review, enums) and
ContractManager._GREP_PATTERNS from contract.py.
"""

import json
import re
from pathlib import Path

import pytest

from outbid_dirigent.contract_schema import (
    AcceptanceCriterion,
    Contract,
    CriterionLayer,
    CriterionResult,
    CriterionVerdict,
    ExpectedFileChange,
    Finding,
    FindingSeverity,
    Review,
    VerificationEvidence,
    Verdict,
)
from outbid_dirigent.contract import ContractManager


# ══════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════

def _make_criterion(id_: str = "AC-01-01", layer: CriterionLayer = CriterionLayer.BEHAVIORAL) -> AcceptanceCriterion:
    return AcceptanceCriterion(
        id=id_,
        description="Something works",
        verification="Run: curl http://localhost:3000/health",
        layer=layer,
    )


def _make_contract(**kwargs) -> Contract:
    defaults = dict(
        phase_id="01",
        phase_name="Bootstrap",
        objective="Get the app running",
        acceptance_criteria=[_make_criterion()],
    )
    defaults.update(kwargs)
    return Contract(**defaults)


def _make_criterion_result(
    ac_id: str = "AC-01-01",
    verdict: CriterionVerdict = CriterionVerdict.PASS,
    evidence: list | None = None,
) -> CriterionResult:
    return CriterionResult(
        ac_id=ac_id,
        verdict=verdict,
        notes="some notes",
        evidence=evidence or [],
    )


def _make_review(**kwargs) -> Review:
    defaults = dict(
        phase_id="01",
        verdict=Verdict.PASS,
        criteria_results=[_make_criterion_result()],
    )
    defaults.update(kwargs)
    return Review(**defaults)


# ══════════════════════════════════════════
# TestContractSaveLoad
# ══════════════════════════════════════════

class TestContractSaveLoad:
    def test_roundtrip(self, tmp_path):
        contract = _make_contract(
            acceptance_criteria=[
                _make_criterion("AC-01-01", CriterionLayer.BEHAVIORAL),
                _make_criterion("AC-01-02", CriterionLayer.BOUNDARY),
            ],
            out_of_scope=["Deployment"],
            expected_files=[ExpectedFileChange(path="src/foo.py", change="Add class")],
        )
        path = tmp_path / "contract.json"
        contract.save(path)
        loaded = Contract.load(path)

        assert loaded is not None
        assert loaded.phase_id == "01"
        assert loaded.phase_name == "Bootstrap"
        assert len(loaded.acceptance_criteria) == 2
        assert loaded.acceptance_criteria[0].layer == CriterionLayer.BEHAVIORAL
        assert loaded.acceptance_criteria[1].layer == CriterionLayer.BOUNDARY
        assert loaded.out_of_scope == ["Deployment"]
        assert loaded.expected_files[0].path == "src/foo.py"

    def test_missing_file_returns_none(self, tmp_path):
        result = Contract.load(tmp_path / "nonexistent.json")
        assert result is None

    def test_backward_compat_category_functional_maps_to_behavioral(self, tmp_path):
        raw = {
            "phase_id": "02",
            "phase_name": "Auth",
            "objective": "Add auth",
            "acceptance_criteria": [
                {
                    "id": "AC-02-01",
                    "description": "Login works",
                    "verification": "Run: curl -X POST /login",
                    "category": "functional",   # old field name
                }
            ],
        }
        path = tmp_path / "contract_old.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Contract.load(path)

        assert loaded is not None
        assert loaded.acceptance_criteria[0].layer == CriterionLayer.BEHAVIORAL

    def test_backward_compat_category_quality_maps_to_structural(self, tmp_path):
        raw = {
            "phase_id": "02",
            "phase_name": "Auth",
            "objective": "Add auth",
            "acceptance_criteria": [
                {
                    "id": "AC-02-01",
                    "description": "Compiles",
                    "verification": "Run: npm run build",
                    "category": "quality",   # old field name
                }
            ],
        }
        path = tmp_path / "contract_quality.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Contract.load(path)

        assert loaded is not None
        assert loaded.acceptance_criteria[0].layer == CriterionLayer.STRUCTURAL

    def test_backward_compat_unknown_category_defaults_to_behavioral(self, tmp_path):
        raw = {
            "phase_id": "02",
            "phase_name": "Auth",
            "objective": "Add auth",
            "acceptance_criteria": [
                {
                    "id": "AC-02-01",
                    "description": "Something",
                    "verification": "Run: echo ok",
                    "category": "unknown_value",
                }
            ],
        }
        path = tmp_path / "contract_unknown.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Contract.load(path)

        assert loaded is not None
        assert loaded.acceptance_criteria[0].layer == CriterionLayer.BEHAVIORAL

    def test_summary_for_prompt_includes_verification(self):
        contract = _make_contract(
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-01-01",
                    description="Health endpoint responds 200",
                    verification="Run: curl -sf http://localhost:3000/health",
                    layer=CriterionLayer.BEHAVIORAL,
                )
            ]
        )
        summary = contract.summary_for_prompt()

        assert "AC-01-01" in summary
        assert "Health endpoint responds 200" in summary
        assert "Run: curl -sf http://localhost:3000/health" in summary
        assert "behavioral" in summary

    def test_summary_for_prompt_includes_phase_id_and_objective(self):
        contract = _make_contract(objective="Set up the database schema")
        summary = contract.summary_for_prompt()

        assert "Phase 01" in summary
        assert "Set up the database schema" in summary


# ══════════════════════════════════════════
# TestReviewComputedProperties
# ══════════════════════════════════════════

class TestReviewComputedProperties:
    def test_critical_count(self):
        review = _make_review(
            findings=[
                Finding(severity=FindingSeverity.CRITICAL, file="a.py", description="Bad"),
                Finding(severity=FindingSeverity.CRITICAL, file="b.py", description="Bad2"),
                Finding(severity=FindingSeverity.WARN, file="c.py", description="Meh"),
                Finding(severity=FindingSeverity.INFO, file="d.py", description="FYI"),
            ]
        )
        assert review.critical_count == 2

    def test_critical_count_zero_when_no_findings(self):
        review = _make_review(findings=[])
        assert review.critical_count == 0

    def test_warn_count(self):
        review = _make_review(
            findings=[
                Finding(severity=FindingSeverity.CRITICAL, file="a.py", description="Bad"),
                Finding(severity=FindingSeverity.WARN, file="b.py", description="Meh"),
                Finding(severity=FindingSeverity.WARN, file="c.py", description="Meh2"),
            ]
        )
        assert review.warn_count == 2

    def test_failed_criteria(self):
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.PASS),
            _make_criterion_result("AC-01-02", CriterionVerdict.FAIL),
            _make_criterion_result("AC-01-03", CriterionVerdict.FAIL),
            _make_criterion_result("AC-01-04", CriterionVerdict.WARN),
        ]
        review = _make_review(criteria_results=results)
        failed = review.failed_criteria

        assert len(failed) == 2
        assert all(r.verdict == CriterionVerdict.FAIL for r in failed)
        assert {r.ac_id for r in failed} == {"AC-01-02", "AC-01-03"}

    def test_passed_criteria(self):
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.PASS),
            _make_criterion_result("AC-01-02", CriterionVerdict.PASS),
            _make_criterion_result("AC-01-03", CriterionVerdict.FAIL),
        ]
        review = _make_review(criteria_results=results)
        passed = review.passed_criteria

        assert len(passed) == 2
        assert all(r.verdict == CriterionVerdict.PASS for r in passed)

    def test_criteria_without_evidence_pass_no_evidence(self):
        """PASS criteria with no evidence show up in criteria_without_evidence."""
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.PASS, evidence=[]),
            _make_criterion_result("AC-01-02", CriterionVerdict.PASS, evidence=[]),
        ]
        review = _make_review(criteria_results=results)
        without_evidence = review.criteria_without_evidence

        assert len(without_evidence) == 2
        assert {r.ac_id for r in without_evidence} == {"AC-01-01", "AC-01-02"}

    def test_criteria_without_evidence_excludes_criteria_with_evidence(self):
        evidence = [VerificationEvidence(command="curl localhost", exit_code=0)]
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.PASS, evidence=evidence),
            _make_criterion_result("AC-01-02", CriterionVerdict.PASS, evidence=[]),
        ]
        review = _make_review(criteria_results=results)
        without_evidence = review.criteria_without_evidence

        assert len(without_evidence) == 1
        assert without_evidence[0].ac_id == "AC-01-02"

    def test_fail_criteria_not_in_criteria_without_evidence(self):
        """FAIL criteria (even without evidence) are excluded from criteria_without_evidence."""
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.FAIL, evidence=[]),
            _make_criterion_result("AC-01-02", CriterionVerdict.FAIL, evidence=[]),
        ]
        review = _make_review(verdict=Verdict.FAIL, criteria_results=results)
        without_evidence = review.criteria_without_evidence

        assert len(without_evidence) == 0

    def test_warn_criteria_not_in_criteria_without_evidence(self):
        """WARN criteria are excluded from criteria_without_evidence (only PASS is tracked)."""
        results = [
            _make_criterion_result("AC-01-01", CriterionVerdict.WARN, evidence=[]),
        ]
        review = _make_review(criteria_results=results)
        assert len(review.criteria_without_evidence) == 0


# ══════════════════════════════════════════
# TestReviewSaveLoad
# ══════════════════════════════════════════

class TestReviewSaveLoad:
    def test_roundtrip(self, tmp_path):
        evidence = VerificationEvidence(
            command="curl localhost:3000/health",
            exit_code=0,
            stdout_snippet='{"status": "ok"}',
            stderr_snippet="",
        )
        review = Review(
            phase_id="01",
            iteration=2,
            verdict=Verdict.PASS,
            confidence="integration",
            criteria_results=[
                CriterionResult(
                    ac_id="AC-01-01",
                    verdict=CriterionVerdict.PASS,
                    notes="All good",
                    evidence=[evidence],
                )
            ],
            findings=[
                Finding(
                    severity=FindingSeverity.WARN,
                    file="src/foo.py",
                    line=42,
                    description="Minor style",
                    suggestion="Use f-string",
                )
            ],
            summary="Phase passed.",
        )
        path = tmp_path / "review.json"
        review.save(path)
        loaded = Review.load(path)

        assert loaded is not None
        assert loaded.phase_id == "01"
        assert loaded.iteration == 2
        assert loaded.verdict == Verdict.PASS
        assert loaded.confidence == "integration"
        assert len(loaded.criteria_results) == 1
        assert loaded.criteria_results[0].evidence[0].command == "curl localhost:3000/health"
        assert loaded.findings[0].severity == FindingSeverity.WARN
        assert loaded.summary == "Phase passed."

    def test_missing_file_returns_none(self, tmp_path):
        result = Review.load(tmp_path / "nope.json")
        assert result is None

    def test_backward_compat_uppercase_verdict(self, tmp_path):
        raw = {
            "phase_id": "01",
            "verdict": "PASS",   # old format: uppercase
            "criteria_results": [],
        }
        path = tmp_path / "review_old_verdict.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Review.load(path)

        assert loaded is not None
        assert loaded.verdict == Verdict.PASS

    def test_backward_compat_uppercase_fail_verdict(self, tmp_path):
        raw = {
            "phase_id": "01",
            "verdict": "FAIL",
            "criteria_results": [],
        }
        path = tmp_path / "review_old_fail.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Review.load(path)

        assert loaded is not None
        assert loaded.verdict == Verdict.FAIL

    def test_backward_compat_results_field(self, tmp_path):
        """Old schema used 'results' field with id/status/actual keys."""
        raw = {
            "phase_id": "01",
            "verdict": "pass",
            "results": [
                {
                    "id": "AC-01-01",
                    "status": "pass",
                    "layer": "behavioral",
                    "actual": "Endpoint returned 200",
                    "notes": "",
                },
                {
                    "id": "AC-01-02",
                    "status": "fail",
                    "layer": "boundary",
                    "actual": "",
                    "notes": "Not implemented",
                },
            ],
        }
        path = tmp_path / "review_old_results.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Review.load(path)

        assert loaded is not None
        assert len(loaded.criteria_results) == 2
        assert loaded.criteria_results[0].ac_id == "AC-01-01"
        assert loaded.criteria_results[0].verdict == CriterionVerdict.PASS
        assert loaded.criteria_results[0].notes == "Endpoint returned 200"
        assert loaded.criteria_results[1].ac_id == "AC-01-02"
        assert loaded.criteria_results[1].verdict == CriterionVerdict.FAIL

    def test_backward_compat_issues_field_severity_mapping(self, tmp_path):
        """Old schema used 'issues' field with high/medium/low severity."""
        raw = {
            "phase_id": "01",
            "verdict": "fail",
            "criteria_results": [],
            "issues": [
                {
                    "severity": "high",
                    "criterion": "src/auth.py",
                    "description": "SQL injection",
                    "recommendation": "Use parameterised queries",
                },
                {
                    "severity": "medium",
                    "criterion": "src/user.py",
                    "description": "Missing validation",
                    "recommendation": "Add input validation",
                },
                {
                    "severity": "low",
                    "criterion": "src/utils.py",
                    "description": "Unused import",
                    "recommendation": "Remove import",
                },
            ],
        }
        path = tmp_path / "review_old_issues.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        loaded = Review.load(path)

        assert loaded is not None
        assert len(loaded.findings) == 3

        severities = {f.file: f.severity for f in loaded.findings}
        assert severities["src/auth.py"] == FindingSeverity.CRITICAL
        assert severities["src/user.py"] == FindingSeverity.WARN
        assert severities["src/utils.py"] == FindingSeverity.INFO

        # Descriptions and suggestions migrate correctly
        auth_finding = next(f for f in loaded.findings if f.file == "src/auth.py")
        assert auth_finding.description == "SQL injection"
        assert auth_finding.suggestion == "Use parameterised queries"


# ══════════════════════════════════════════
# TestGrepPatterns
# ══════════════════════════════════════════

class TestGrepPatterns:
    """Test ContractManager._GREP_PATTERNS detects structural-check anti-patterns."""

    PATTERN = ContractManager._GREP_PATTERNS

    # ── should detect ──────────────────────────────────────────

    @pytest.mark.parametrize("cmd", [
        "grep 'def login' src/auth.py",
        "grep -r UserController app/",
        "rg 'import React' src/",
        "ag 'class Foo'",
        "ack 'TODO'",
    ])
    def test_detects_grep_variants(self, cmd):
        assert self.PATTERN.search(cmd), f"Expected match for: {cmd!r}"

    @pytest.mark.parametrize("cmd", [
        "cat src/app.py",
        "head src/index.ts",
        "tail src/main.js",
        "cat src/component.tsx",
        "head src/lib.jsx",
        "cat src/server.go",
        "cat src/main.rs",
        "cat src/Service.java",
    ])
    def test_detects_cat_head_tail_on_source_files(self, cmd):
        assert self.PATTERN.search(cmd), f"Expected match for: {cmd!r}"

    @pytest.mark.parametrize("cmd", [
        "test -f /tmp/output.log",
        "test -e /var/run/app.pid",
        "test -d /tmp/builds",
    ])
    def test_detects_test_flag_checks(self, cmd):
        assert self.PATTERN.search(cmd), f"Expected match for: {cmd!r}"

    @pytest.mark.parametrize("cmd", [
        "[ -f /tmp/output.log ] && echo exists",
        "[ -e /var/run/pid ]",
        "[ -d /tmp/data ]",
    ])
    def test_detects_bracket_file_checks(self, cmd):
        assert self.PATTERN.search(cmd), f"Expected match for: {cmd!r}"

    # ── should NOT detect ──────────────────────────────────────

    @pytest.mark.parametrize("cmd", [
        "curl -sf http://localhost:3000/health",
        "npm run test",
        "pytest tests/ -v",
        "python -m pytest",
        "npx jest",
        "go test ./...",
        "cargo test",
        "bundle exec rspec",
    ])
    def test_allows_legitimate_test_commands(self, cmd):
        assert not self.PATTERN.search(cmd), f"Expected no match for: {cmd!r}"

    @pytest.mark.parametrize("cmd", [
        "cat /tmp/output.log",           # cat on non-source file (no extension match)
        "head /var/log/app.log",          # head on .log file
        "tail /tmp/results.txt",          # tail on .txt file
    ])
    def test_allows_cat_on_non_source_files(self, cmd):
        assert not self.PATTERN.search(cmd), f"Expected no match for: {cmd!r}"
