"""Regression guards for Claude Code plugin-agent frontmatter.

The `tools:` list in an agent's frontmatter is filtered exactly like the
top-level `allowed_tools` — a bare `mcp__context7` matches nothing because
real MCP tools are named `mcp__<server>__<tool>`. We've shipped this bug
twice already (once in task_runner.py, once in implementer.md); these tests
keep the third occurrence from sneaking in.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENTS_DIR = Path(__file__).parent.parent / "src" / "outbid_dirigent" / "plugin" / "agents"

# Tool entries that are legal as-is in a frontmatter `tools:` list.
# Core tools + Skill + Agent are plain names. MCP tools must either be a
# fully-qualified `mcp__<server>__<tool>` or a wildcard `mcp__<server>__*`.
_LEGAL_NON_MCP = {
    "Read", "Write", "Edit", "Bash", "Glob", "Grep",
    "WebFetch", "WebSearch", "Skill", "Agent",
    "TodoWrite", "NotebookEdit", "KillShell", "BashOutput",
    "ExitPlanMode", "ListMcpResourcesTool", "ReadMcpResourceTool",
}


def _parse_frontmatter_tools(path: Path) -> list[str] | None:
    """Extract the `tools:` line from the first YAML frontmatter block. Returns None if absent."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    for line in text[4:end].splitlines():
        if line.startswith("tools:"):
            raw = line.split(":", 1)[1].strip()
            return [t.strip() for t in raw.split(",") if t.strip()]
    return None


def _agent_files() -> list[Path]:
    return sorted(AGENTS_DIR.glob("*.md"))


@pytest.mark.parametrize("agent_path", _agent_files(), ids=lambda p: p.name)
def test_no_bare_mcp_prefix_in_frontmatter(agent_path: Path):
    """Every `mcp__<...>` entry must be a full `mcp__<server>__<tool>` or wildcard `mcp__<server>__*`.

    Bare `mcp__context7` (no `__tool` or `__*` suffix) silently filters out
    every real context7 call — we shipped exactly this bug in implementer.md
    and plugin-writer.md, fixed alongside this test.
    """
    tools = _parse_frontmatter_tools(agent_path)
    if tools is None:
        pytest.skip(f"{agent_path.name} has no tools: field (inherits)")

    bare_mcp = [
        t for t in tools
        if t.startswith("mcp__") and not re.fullmatch(r"mcp__[a-zA-Z0-9_]+__(\*|[a-zA-Z0-9_-]+)", t)
    ]
    assert not bare_mcp, (
        f"{agent_path.name}: bare mcp__ entries without __* or full tool name: {bare_mcp}"
    )


@pytest.mark.parametrize("agent_path", _agent_files(), ids=lambda p: p.name)
def test_only_known_tool_names_or_mcp_pattern(agent_path: Path):
    """Catch typos like `mcp_context7` (single underscore) or misspelled core tools."""
    tools = _parse_frontmatter_tools(agent_path)
    if tools is None:
        pytest.skip(f"{agent_path.name} has no tools: field (inherits)")

    unknown = [
        t for t in tools
        if t not in _LEGAL_NON_MCP and not t.startswith("mcp__")
    ]
    assert not unknown, (
        f"{agent_path.name}: unrecognised tool entries: {unknown}. "
        f"Add to _LEGAL_NON_MCP if this is a new core tool, or fix the typo."
    )


def test_implementer_has_context7_and_playwright_wildcards():
    """Positive assertion: implementer MUST carry context7 AND playwright wildcards.

    Implementer writes both app code (wants context7 for API/syntax recall) and
    Playwright specs (wants playwright-MCP for browser introspection during debug).
    Both install shapes — flat and plugin-namespaced — must be whitelisted.
    """
    path = AGENTS_DIR / "implementer.md"
    tools = _parse_frontmatter_tools(path)
    assert tools is not None, "implementer.md must have tools: field"
    required = {
        "mcp__context7__*",
        "mcp__plugin_context7_context7__*",
        "mcp__playwright__*",
        "mcp__plugin_playwright_playwright__*",
    }
    missing = required - set(tools)
    assert not missing, f"implementer.md missing MCP wildcards: {missing}"
