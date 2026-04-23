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


def test_implementer_context7_instruction_is_unconditional():
    """Regression guard: the context7 instruction must not regress to weak/conditional wording.

    The previous soft wording "Before guessing at API shapes..." let the model decide
    it wasn't guessing and skip the tool every time. After v2.2.2 a real run shipped a
    stale-Server-Component bug because context7 was never called. The fix is
    unconditional imperative wording — these assertions keep that in place.
    """
    body = (AGENTS_DIR / "implementer.md").read_text(encoding="utf-8")

    # Must NOT contain the old soft phrasing
    assert "Before guessing at API shapes" not in body, (
        "implementer.md regressed to conditional 'Before guessing' wording — "
        "this was the exact phrasing that produced zero context7 calls across 13 tasks."
    )

    # MUST carry an unconditional marker and explicit framework list
    must_contain = [
        "MANDATORY",  # imperative marker
        "mcp__context7__resolve-library-id",  # the call is spelled out
        "mcp__context7__query-docs",
        "Next.js",  # version-sensitive framework named
        "Supabase",  # version-sensitive framework named
    ]
    for phrase in must_contain:
        assert phrase in body, (
            f"implementer.md missing required phrase {phrase!r} in context7 "
            f"instruction — may have regressed."
        )


def test_implementer_review_fix_forbids_loosening_tests():
    """Regression guard: the review-fix loop must forbid test-assertion loosening.

    The failure mode we shipped: implementer sees a spec assertion fail during
    review-fix, deletes/weakens the assertion instead of fixing the code, review
    passes on an empty dashboard. The implementer.md Review-Fix section now
    enumerates this as forbidden; these assertions keep that in place.
    """
    body = (AGENTS_DIR / "implementer.md").read_text(encoding="utf-8")

    # Hard-forbid section must name the anti-pattern explicitly
    must_contain = [
        "FORBIDDEN",  # imperative marker in the section heading
        "loosening or removing test assertions",
        "WEAKEN",
        "DELETE",
        "fix the code",  # the positive alternative
        "DEVIATION: Contract-Concern",  # escape hatch when contract is genuinely wrong
    ]
    for phrase in must_contain:
        assert phrase in body, (
            f"implementer.md review-fix section missing {phrase!r} — "
            f"test-loosening forbid may have regressed."
        )


def test_implement_task_skill_context7_instruction_is_unconditional():
    """Mirror of the above for the skill-level instruction.

    The skill body is loaded into the implementer's prompt upstream of the agent
    frontmatter — both must carry imperative wording so the instruction isn't
    reasoned away before the agent sees it.
    """
    skill_path = (
        AGENTS_DIR.parent
        / "skills"
        / "implement-task"
        / "SKILL.md"
    )
    assert skill_path.exists(), f"expected {skill_path} to exist"
    body = skill_path.read_text(encoding="utf-8")

    # Must NOT contain the old soft gating
    for weak_phrase in [
        "Use it for any tool you're about to install",  # conditional on install
    ]:
        assert weak_phrase not in body, (
            f"implement-task/SKILL.md regressed to weak wording: {weak_phrase!r}"
        )

    # MUST carry imperative markers
    for phrase in ["MANDATORY", "Not optional", "mcp__context7__resolve-library-id"]:
        assert phrase in body, (
            f"implement-task/SKILL.md missing required phrase {phrase!r}"
        )
