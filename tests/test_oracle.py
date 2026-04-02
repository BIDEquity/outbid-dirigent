"""Unit tests for Oracle cache logic (no API calls)."""

import json
import hashlib
from pathlib import Path

import pytest

from outbid_dirigent.oracle import Oracle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_oracle(tmp_path: Path) -> Oracle:
    """Instantiate Oracle bypassing __init__ to avoid Anthropic client creation."""
    (tmp_path / ".dirigent").mkdir(exist_ok=True)
    oracle = Oracle.__new__(Oracle)
    oracle.repo_path = tmp_path
    oracle.model = "test-model"
    oracle.logger = type("L", (), {
        k: (lambda *a, **kw: None)
        for k in ["debug", "info", "error", "oracle_query", "oracle_decision", "api_usage", "warn"]
    })()
    oracle.decisions_file = tmp_path / ".dirigent" / "DECISIONS.json"
    oracle.decisions = {"decisions": [], "created_at": "2026-04-02T10:00:00"}
    return oracle


# ---------------------------------------------------------------------------
# TestGetCacheKey
# ---------------------------------------------------------------------------

class TestGetCacheKey:
    def test_deterministic(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        key1 = oracle._get_cache_key("Which database?", ["postgres", "mysql"])
        key2 = oracle._get_cache_key("Which database?", ["postgres", "mysql"])
        assert key1 == key2

    def test_options_order_independent(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        key1 = oracle._get_cache_key("Which database?", ["postgres", "mysql"])
        key2 = oracle._get_cache_key("Which database?", ["mysql", "postgres"])
        assert key1 == key2

    def test_different_questions_give_different_keys(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        key1 = oracle._get_cache_key("Which database?", ["postgres"])
        key2 = oracle._get_cache_key("Which framework?", ["postgres"])
        assert key1 != key2

    def test_key_is_16_char_hex(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        key = oracle._get_cache_key("Some question", ["opt1", "opt2"])
        assert len(key) == 16
        assert all(c in "0123456789abcdef" for c in key)

    def test_matches_manual_sha256(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        question = "Which database?"
        options = ["mysql", "postgres"]
        expected_content = f"{question}|{'|'.join(sorted(options))}"
        expected = hashlib.sha256(expected_content.encode()).hexdigest()[:16]
        assert oracle._get_cache_key(question, options) == expected


# ---------------------------------------------------------------------------
# TestCheckCache
# ---------------------------------------------------------------------------

class TestCheckCache:
    def test_cache_hit_returns_dict(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        entry = {
            "cache_key": "abc123def456abcd",
            "question": "Which database?",
            "decision": "postgres",
            "reason": "Best choice",
        }
        oracle.decisions["decisions"].append(entry)
        result = oracle._check_cache("abc123def456abcd")
        assert result is not None
        assert result["decision"] == "postgres"

    def test_cache_miss_returns_none(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        entry = {
            "cache_key": "abc123def456abcd",
            "question": "Which database?",
            "decision": "postgres",
            "reason": "Best choice",
        }
        oracle.decisions["decisions"].append(entry)
        result = oracle._check_cache("0000000000000000")
        assert result is None

    def test_empty_cache_returns_none(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        assert oracle._check_cache("anykey123456abcd") is None

    def test_returns_correct_entry_among_multiple(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle.decisions["decisions"] = [
            {"cache_key": "key1111111111111", "decision": "A", "reason": "r"},
            {"cache_key": "key2222222222222", "decision": "B", "reason": "r"},
            {"cache_key": "key3333333333333", "decision": "C", "reason": "r"},
        ]
        result = oracle._check_cache("key2222222222222")
        assert result["decision"] == "B"


# ---------------------------------------------------------------------------
# TestRelevantDecisions
# ---------------------------------------------------------------------------

class TestRelevantDecisions:
    def _make_decision(self, question: str, decision: str = "X") -> dict:
        return {
            "cache_key": "0000000000000000",
            "question": question,
            "decision": decision,
            "reason": "reason",
        }

    def test_empty_decisions_returns_empty_list(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        result = oracle._relevant_decisions("database engine choice")
        assert result == []

    def test_database_questions_rank_higher_for_database_query(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        decisions = [
            self._make_decision("which css framework to use"),
            self._make_decision("which database engine to use"),
            self._make_decision("which logging library to use"),
            self._make_decision("which database driver to choose"),
        ]
        oracle.decisions["decisions"] = decisions
        result = oracle._relevant_decisions("database engine choice", top_n=2)
        questions = [d["question"] for d in result]
        assert "which database engine to use" in questions

    def test_most_recent_always_included(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        # Fill with 10 unrelated decisions, last one is about "css"
        decisions = [self._make_decision(f"database question {i}") for i in range(9)]
        last = self._make_decision("which css preprocessor to use")
        decisions.append(last)
        oracle.decisions["decisions"] = decisions
        # Query is database-heavy, so last entry has low relevance
        result = oracle._relevant_decisions("database engine choice", top_n=5)
        assert last in result

    def test_respects_top_n_limit(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle.decisions["decisions"] = [
            self._make_decision(f"question {i}") for i in range(20)
        ]
        result = oracle._relevant_decisions("question relevance", top_n=5)
        assert len(result) <= 5

    def test_single_decision_always_returned(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        d = self._make_decision("something completely unrelated")
        oracle.decisions["decisions"] = [d]
        result = oracle._relevant_decisions("database engine", top_n=8)
        assert d in result


# ---------------------------------------------------------------------------
# TestSaveLoadDecisions
# ---------------------------------------------------------------------------

class TestSaveLoadDecisions:
    def test_save_and_reload_roundtrip(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle.decisions["decisions"].append({
            "cache_key": "abc123def456abcd",
            "question": "Which database?",
            "decision": "postgres",
            "reason": "Best choice",
            "confidence": "high",
        })
        oracle._save_decisions()

        # Reload via _load_decisions
        oracle2 = _make_oracle(tmp_path)
        loaded = oracle2._load_decisions()
        assert len(loaded["decisions"]) == 1
        assert loaded["decisions"][0]["decision"] == "postgres"

    def test_save_writes_updated_at(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle._save_decisions()
        data = json.loads(oracle.decisions_file.read_text())
        assert "updated_at" in data

    def test_load_returns_empty_when_no_file(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        # File doesn't exist yet
        loaded = oracle._load_decisions()
        assert loaded["decisions"] == []

    def test_clear_cache_empties_decisions(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle.decisions["decisions"].append({
            "cache_key": "abc123def456abcd",
            "question": "Q",
            "decision": "D",
            "reason": "R",
        })
        oracle.clear_cache()
        assert oracle.decisions["decisions"] == []

    def test_clear_cache_persists_to_file(self, tmp_path):
        oracle = _make_oracle(tmp_path)
        oracle.decisions["decisions"].append({
            "cache_key": "abc123def456abcd",
            "question": "Q",
            "decision": "D",
            "reason": "R",
        })
        oracle._save_decisions()
        oracle.clear_cache()
        # Re-read from file
        data = json.loads(oracle.decisions_file.read_text())
        assert data["decisions"] == []
