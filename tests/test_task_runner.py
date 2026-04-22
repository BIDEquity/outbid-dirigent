"""Unit tests for TaskRunner static helpers and TaskResult data class."""

import re

from outbid_dirigent.task_runner import TaskResult, TaskRunner


class TestDefaultAllowedTools:
    """Every Claude Code subprocess spawned by dirigent flows through _run_claude,
    which uses TaskRunner.DEFAULT_ALLOWED_TOOLS as its whitelist. Wrong entries here
    silently block skill-referenced MCP tools (context7, playwright) at the filter
    even when the servers are ✓ Connected — we observed exactly this in a greenfield
    run where `mcp__context7` alone was listed and no context7 call ever succeeded.
    """

    def test_core_tools_present(self):
        for t in ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]:
            assert t in TaskRunner.DEFAULT_ALLOWED_TOOLS, f"missing core tool {t}"

    def test_context7_entries_use_wildcard_suffix(self):
        """`mcp__context7` alone matches nothing — must be `mcp__<server>__*` shape."""
        ctx7 = [t for t in TaskRunner.DEFAULT_ALLOWED_TOOLS if "context7" in t]
        assert ctx7, "no context7 entry at all"
        for t in ctx7:
            assert re.fullmatch(
                r"mcp__[a-zA-Z0-9_]+__\*", t
            ), f"context7 entry {t!r} is not an mcp__<server>__* pattern"

    def test_covers_flat_and_plugin_namespaced_installs(self):
        """context7 and playwright can be installed either as flat MCP servers or
        via Claude Code plugins (which add an extra `plugin_<name>_<name>` namespace).
        Both shapes must be whitelisted so skill prose works in either environment.
        """
        required = {
            "mcp__context7__*",
            "mcp__plugin_context7_context7__*",
            "mcp__playwright__*",
            "mcp__plugin_playwright_playwright__*",
        }
        missing = required - set(TaskRunner.DEFAULT_ALLOWED_TOOLS)
        assert not missing, f"missing MCP patterns: {missing}"

    def test_no_bare_mcp_prefix_without_wildcard(self):
        """Regression guard: `mcp__context7` (no `__*`) matches nothing in Claude
        Code's allowed_tools filter. Every mcp__-prefixed entry must either be a
        fully-qualified tool name or end with `__*`.
        """
        bad = [
            t
            for t in TaskRunner.DEFAULT_ALLOWED_TOOLS
            if t.startswith("mcp__") and not t.endswith("__*") and t.count("__") < 2
        ]
        assert not bad, f"bare mcp__ prefixes without __* or full tool name: {bad}"


class TestExtractDeviations:
    def test_single_deviation_dash_separator(self):
        summary = "DEVIATION: bug-fix - Fixed null pointer in auth module"
        result = TaskRunner._extract_deviations(summary)
        assert len(result) == 1
        assert result[0]["type"] == "bug-fix"
        assert "null pointer" in result[0]["description"]

    def test_multiple_deviations(self):
        summary = (
            "Some text\n"
            "DEVIATION: bug-fix - Fixed null pointer in auth module\n"
            "More text\n"
            "DEVIATION: refactor: Extracted helper function\n"
        )
        result = TaskRunner._extract_deviations(summary)
        assert len(result) == 2
        types = {d["type"] for d in result}
        assert types == {"bug-fix", "refactor"}

    def test_no_deviations_returns_empty_list(self):
        summary = "Everything went smoothly. No issues found."
        result = TaskRunner._extract_deviations(summary)
        assert result == []

    def test_case_insensitive(self):
        summary = "deviation: Bug-Fix: something went differently"
        result = TaskRunner._extract_deviations(summary)
        assert len(result) == 1
        assert result[0]["type"] == "Bug-Fix"
        assert "something went differently" in result[0]["description"]

    def test_colon_separator(self):
        summary = "DEVIATION: refactor: Extracted helper function"
        result = TaskRunner._extract_deviations(summary)
        assert len(result) == 1
        assert result[0]["type"] == "refactor"
        assert "Extracted helper function" in result[0]["description"]

    def test_empty_string(self):
        assert TaskRunner._extract_deviations("") == []


class TestTaskResult:
    def test_default_values(self):
        result = TaskResult(task_id="t-01", success=True)
        assert result.task_id == "t-01"
        assert result.success is True
        assert result.commit_hash is None
        assert result.summary == ""
        assert result.deviations == []
        assert result.duration_seconds == 0
        assert result.attempts == 1

    def test_deviations_default_is_independent_list(self):
        r1 = TaskResult(task_id="a", success=True)
        r2 = TaskResult(task_id="b", success=True)
        r1.deviations.append({"type": "x", "description": "y"})
        assert r2.deviations == [], "default deviations list must not be shared between instances"

    def test_failed_result(self):
        result = TaskResult(task_id="t-02", success=False, attempts=3)
        assert result.success is False
        assert result.attempts == 3
        assert result.commit_hash is None

    def test_explicit_values(self):
        devs = [{"type": "refactor", "description": "Extracted helper"}]
        result = TaskResult(
            task_id="t-03",
            success=True,
            commit_hash="abc123",
            summary="All done",
            deviations=devs,
            duration_seconds=42.5,
            attempts=2,
        )
        assert result.commit_hash == "abc123"
        assert result.summary == "All done"
        assert result.deviations == devs
        assert result.duration_seconds == 42.5
        assert result.attempts == 2
