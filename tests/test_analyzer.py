"""
Unit tests for analyzer.py — pure logic, no filesystem or git calls.
"""

import pytest
from pathlib import Path
from typing import List

from outbid_dirigent.analyzer import (
    Analyzer,
    RepoAnalysis,
    SpecAnalysis,
)


# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_repo(**overrides) -> RepoAnalysis:
    defaults = dict(
        repo_path="/tmp/test",
        repo_name="test",
        primary_language="TypeScript",
        secondary_languages=[],
        framework_detected=None,
        build_tool=None,
        commit_count=100,
        last_commit_days_ago=5,
        last_commit_date="2026-03-28",
        file_count=30,
        total_lines=5000,
        has_tests=True,
        has_ci=True,
        directories=["src"],
        config_files=["package.json"],
    )
    defaults.update(overrides)
    return RepoAnalysis(**defaults)


def _make_spec(**overrides) -> SpecAnalysis:
    defaults = dict(
        spec_path="/tmp/spec.md",
        title="Test Spec",
        has_legacy_keywords=False,
        has_greenfield_keywords=False,
        has_testability_keywords=False,
        has_tracking_keywords=False,
        legacy_keywords_found=[],
        greenfield_keywords_found=[],
        testability_keywords_found=[],
        tracking_keywords_found=[],
        target_language=None,
        complexity=None,
        estimated_scope="small",
    )
    defaults.update(overrides)
    return SpecAnalysis(**defaults)


def _make_analyzer() -> Analyzer:
    """Create an Analyzer without calling __init__ (which requires real paths)."""
    return Analyzer.__new__(Analyzer)


# ─── TestDetermineRoute ──────────────────────────────────────────────────────


class TestDetermineRoute:

    def test_testability_route_two_keywords(self):
        analyzer = _make_analyzer()
        spec = _make_spec(
            has_testability_keywords=True,
            testability_keywords_found=["add tests", "test coverage"],
        )
        route, reason, confidence, legacy, greenfield = analyzer._determine_route(_make_repo(), spec)
        assert route == "testability"
        assert confidence == "high"

    def test_testability_needs_at_least_two_keywords(self):
        analyzer = _make_analyzer()
        spec = _make_spec(
            has_testability_keywords=True,
            testability_keywords_found=["add tests"],  # only 1 → not testability
        )
        route, _, _, _, _ = analyzer._determine_route(_make_repo(), spec)
        assert route != "testability"

    def test_tracking_route_two_keywords(self):
        analyzer = _make_analyzer()
        spec = _make_spec(
            has_tracking_keywords=True,
            tracking_keywords_found=["posthog", "event tracking"],
        )
        route, reason, confidence, legacy, greenfield = analyzer._determine_route(_make_repo(), spec)
        assert route == "tracking"
        assert confidence == "high"

    def test_inactive_repo_adds_legacy_signals(self):
        analyzer = _make_analyzer()
        repo = _make_repo(last_commit_days_ago=400)  # > 365
        _, _, _, legacy, _ = analyzer._determine_route(repo, _make_spec())
        assert legacy >= 2

    def test_language_migration_ruby_to_typescript_adds_legacy_signals(self):
        analyzer = _make_analyzer()
        repo = _make_repo(primary_language="Ruby")
        spec = _make_spec(target_language="TypeScript")
        _, _, _, legacy, _ = analyzer._determine_route(repo, spec)
        assert legacy >= 3

    def test_many_legacy_keywords_inactive_large_commits_gives_legacy_route(self):
        analyzer = _make_analyzer()
        repo = _make_repo(
            last_commit_days_ago=400,   # +2 legacy
            commit_count=2500,          # +1 legacy
        )
        spec = _make_spec(
            has_legacy_keywords=True,
            legacy_keywords_found=["refactor", "migrate", "rewrite"],  # 3+ → +2 legacy
        )
        route, _, _, legacy, _ = analyzer._determine_route(repo, spec)
        assert route == "legacy"
        assert legacy >= 4

    def test_large_commit_count_adds_legacy_signal(self):
        analyzer = _make_analyzer()
        repo = _make_repo(commit_count=2500)  # > 2000
        _, _, _, legacy_with, _ = analyzer._determine_route(repo, _make_spec())

        repo_small = _make_repo(commit_count=100)
        _, _, _, legacy_without, _ = analyzer._determine_route(repo_small, _make_spec())

        assert legacy_with > legacy_without

    def test_active_small_ts_repo_with_greenfield_keywords_gives_greenfield_route(self):
        analyzer = _make_analyzer()
        repo = _make_repo(
            primary_language="TypeScript",
            last_commit_days_ago=10,  # active → +1 greenfield
            file_count=20,            # small → +1 greenfield
        )
        spec = _make_spec(
            has_greenfield_keywords=True,
            greenfield_keywords_found=["add", "create", "implement"],  # +2 greenfield
        )
        route, _, _, _, greenfield = analyzer._determine_route(repo, spec)
        assert route == "greenfield"
        assert greenfield >= 3

    def test_modern_language_adds_greenfield_signal(self):
        analyzer = _make_analyzer()
        for lang in ["TypeScript", "JavaScript", "Python", "Go", "Rust"]:
            repo = _make_repo(primary_language=lang)
            _, _, _, _, greenfield = analyzer._determine_route(repo, _make_spec())
            assert greenfield >= 1, f"Expected greenfield signal for {lang}"

    def test_ambiguous_signals_give_hybrid_route(self):
        analyzer = _make_analyzer()
        # No strong signals in either direction
        repo = _make_repo(
            primary_language="Java",   # not a modern lang
            last_commit_days_ago=100,  # not active (<90), not inactive (>365)
            commit_count=50,
            file_count=100,            # not small
        )
        spec = _make_spec()  # no keywords at all
        route, _, confidence, legacy, greenfield = analyzer._determine_route(repo, spec)
        assert route == "hybrid"
        assert confidence == "medium"


# ─── TestDetectLanguages ─────────────────────────────────────────────────────


class TestDetectLanguages:

    def test_most_common_extension_wins(self):
        analyzer = _make_analyzer()
        files: List[Path] = (
            [Path(f"src/a{i}.ts") for i in range(5)]
            + [Path(f"src/b{i}.py") for i in range(2)]
        )
        primary, secondary = analyzer._detect_languages(files)
        assert primary == "TypeScript"
        assert "Python" in secondary

    def test_empty_list_returns_unknown(self):
        analyzer = _make_analyzer()
        primary, secondary = analyzer._detect_languages([])
        assert primary == "Unknown"
        assert secondary == []

    def test_non_code_files_return_unknown(self):
        analyzer = _make_analyzer()
        files = [Path("README.md"), Path("image.png"), Path("data.csv")]
        primary, secondary = analyzer._detect_languages(files)
        assert primary == "Unknown"
        assert secondary == []


# ─── TestAnalyzeSpec ─────────────────────────────────────────────────────────


class TestAnalyzeSpec:

    def _make_spec_file(self, tmp_path: Path, content: str) -> Analyzer:
        spec_file = tmp_path / "spec.md"
        spec_file.write_text(content, encoding="utf-8")
        analyzer = _make_analyzer()
        analyzer.spec_path = spec_file
        return analyzer

    def test_title_from_first_h1(self, tmp_path):
        analyzer = self._make_spec_file(tmp_path, "# My Feature Title\n\nSome text.")
        result = analyzer._analyze_spec()
        assert result.title == "My Feature Title"

    def test_no_h1_gives_default_title(self, tmp_path):
        analyzer = self._make_spec_file(tmp_path, "Some text without a heading.")
        result = analyzer._analyze_spec()
        assert result.title == "Unbekannt"

    def test_legacy_keywords_detected(self, tmp_path):
        analyzer = self._make_spec_file(
            tmp_path,
            "# Spec\n\nWe need to refactor and migrate the existing system.",
        )
        result = analyzer._analyze_spec()
        assert result.has_legacy_keywords is True
        assert "refactor" in result.legacy_keywords_found
        assert "migrate" in result.legacy_keywords_found

    def test_greenfield_keywords_detected(self, tmp_path):
        analyzer = self._make_spec_file(
            tmp_path,
            "# Spec\n\nAdd a new feature. Create a dashboard.",
        )
        result = analyzer._analyze_spec()
        assert result.has_greenfield_keywords is True
        assert "add" in result.greenfield_keywords_found

    def test_german_greenfield_keywords(self, tmp_path):
        analyzer = self._make_spec_file(
            tmp_path,
            "# Feature\n\nWir möchten eine neue Komponente erstellen und hinzufügen.",
        )
        result = analyzer._analyze_spec()
        assert result.has_greenfield_keywords is True
        assert any(kw in result.greenfield_keywords_found for kw in ["erstellen", "hinzufügen"])

    def test_scope_small_under_200_words(self, tmp_path):
        analyzer = self._make_spec_file(tmp_path, "# Short\n\n" + " ".join(["word"] * 50))
        result = analyzer._analyze_spec()
        assert result.estimated_scope == "small"

    def test_scope_medium_200_to_500_words(self, tmp_path):
        analyzer = self._make_spec_file(tmp_path, "# Medium\n\n" + " ".join(["word"] * 350))
        result = analyzer._analyze_spec()
        assert result.estimated_scope == "medium"

    def test_scope_large_over_500_words(self, tmp_path):
        analyzer = self._make_spec_file(tmp_path, "# Large\n\n" + " ".join(["word"] * 600))
        result = analyzer._analyze_spec()
        assert result.estimated_scope == "large"

    def test_target_language_detected_via_fastapi(self, tmp_path):
        analyzer = self._make_spec_file(
            tmp_path, "# API\n\nBuild an endpoint using FastAPI."
        )
        result = analyzer._analyze_spec()
        assert result.target_language == "Python"

    def test_complexity_extracted(self, tmp_path):
        analyzer = self._make_spec_file(
            tmp_path, "# Feature\n\nComplexity: high\n\nSome description."
        )
        result = analyzer._analyze_spec()
        assert result.complexity == "high"
