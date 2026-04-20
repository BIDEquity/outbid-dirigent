#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "mcp>=1.2.0",
# ]
# ///
"""Dirigent State MCP server.

Exposes the current dirigent run state as MCP resources so the agent can read
spec/plan/state/progress at any time without requiring the user to invoke
slash commands. Resources resolve relative to the *client's* current working
directory at request time, not the server's startup cwd, so a single server
process can serve any repo the user opens.

Resources:
    dirigent://spec        — .dirigent/SPEC.md (raw markdown)
    dirigent://plan        — .dirigent/PLAN.json (raw JSON)
    dirigent://state       — .dirigent/STATE.json (raw JSON)
    dirigent://progress    — computed compact summary (current phase/task, % done)
    dirigent://summaries   — concatenated task summaries (.dirigent/summaries/*.md)

Tools:
    dirigent_status()      — structured snapshot dict (mode, current phase, dirty git, etc.)
    dirigent_show_plan()   — formatted plan rendering matching /dirigent:show-plan output

This is intentionally small. It is NOT a full dirigent driver — only a read-only
window into state. Mutations still go through the dirigent CLI or skills.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

# mcp is provided by the inline uv-script `///script` block above and is NOT
# part of the parent project's dependency closure. Static type checkers running
# against the main package cannot see it; that is fine — this file is executed
# only via `uv run --script` which resolves the inline deps at runtime.
import importlib

FastMCP = importlib.import_module("mcp.server.fastmcp").FastMCP

mcp = FastMCP("dirigent-state")


def _cwd() -> Path:
    """Resolve the cwd of the *user's* shell, not the server.

    The MCP server starts once and serves many repos. We use the env var
    set by Claude Code per request, falling back to the process cwd.
    """
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def _dirigent_dir() -> Path:
    return _cwd() / ".dirigent"


def _read_text_safe(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _read_json_safe(p: Path) -> dict[str, Any] | None:
    text = _read_text_safe(p)
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ---------- resources ----------


@mcp.resource("dirigent://spec")
def spec_resource() -> str:
    """The current SPEC.md, or a hint if none exists."""
    text = _read_text_safe(_dirigent_dir() / "SPEC.md")
    if text is None:
        return (
            "(no SPEC.md in .dirigent/ — run /dirigent:hi or /dirigent:generate-spec to create one)"
        )
    return text


@mcp.resource("dirigent://plan")
def plan_resource() -> str:
    """The current PLAN.json, raw."""
    text = _read_text_safe(_dirigent_dir() / "PLAN.json")
    if text is None:
        return "(no PLAN.json — run /dirigent:create-plan after writing a SPEC)"
    return text


@mcp.resource("dirigent://state")
def state_resource() -> str:
    """The current STATE.json, raw."""
    text = _read_text_safe(_dirigent_dir() / "STATE.json")
    if text is None:
        return "(no STATE.json — no dirigent run has started in this repo)"
    return text


@mcp.resource("dirigent://progress")
def progress_resource() -> str:
    """Compact human-readable progress summary."""
    plan = _read_json_safe(_dirigent_dir() / "PLAN.json")
    state = _read_json_safe(_dirigent_dir() / "STATE.json")

    if plan is None:
        return "No plan in this repo. Start with /dirigent:hi."

    phases = plan.get("phases", [])
    total_phases = len(phases)
    total_tasks = sum(len(p.get("tasks", [])) for p in phases)

    cur_phase = None
    cur_task = None
    completed = 0
    if state is not None:
        cur_phase = (
            state.get("current_phase_id") or state.get("current_phase") or state.get("phase")
        )
        cur_task = state.get("current_task_id") or state.get("current_task")
        completed = len(state.get("completed_tasks", []) or [])

    pct = (completed * 100 // total_tasks) if total_tasks else 0

    lines = [
        f"Plan: {plan.get('title', '(untitled)')}",
        f"Phases: {total_phases}  |  Tasks: {total_tasks}  |  Done: {completed} ({pct}%)",
    ]
    if cur_phase:
        lines.append(f"Current: phase {cur_phase}" + (f" / task {cur_task}" if cur_task else ""))
    return "\n".join(lines)


@mcp.resource("dirigent://summaries")
def summaries_resource() -> str:
    """Concatenated per-task summaries from completed runs."""
    summaries_dir = _dirigent_dir() / "summaries"
    if not summaries_dir.is_dir():
        return "(no task summaries yet)"
    parts: list[str] = []
    for path in sorted(summaries_dir.glob("*.md")):
        text = _read_text_safe(path)
        if text:
            parts.append(f"# {path.stem}\n\n{text}")
    if not parts:
        return "(no task summaries yet)"
    return "\n\n---\n\n".join(parts)


# ---------- tools ----------


@mcp.tool()
def dirigent_status() -> dict[str, Any]:
    """Structured snapshot of current dirigent state in the user's cwd.

    Returns mode (onboarding/continue/resume/recovery/welcome-back),
    plus flags for SPEC/PLAN/STATE presence and git dirty status.
    """
    cwd = _cwd()
    d = cwd / ".dirigent"
    has_dir = d.is_dir()
    has_spec = (d / "SPEC.md").is_file()
    has_plan = (d / "PLAN.json").is_file()
    has_state = (d / "STATE.json").is_file()
    has_summaries = (d / "summaries").is_dir() and any((d / "summaries").glob("*.md"))

    git_dirty = False
    try:
        out = subprocess.run(
            ["git", "-C", str(cwd), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        git_dirty = bool(out.stdout.strip())
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    if has_plan and has_state:
        mode = "resume"
    elif has_spec and not has_plan:
        mode = "continue"
    elif has_summaries and git_dirty:
        mode = "recovery"
    elif has_dir:
        mode = "welcome-back"
    else:
        mode = "onboarding"

    return {
        "cwd": str(cwd),
        "mode": mode,
        "has_dirigent_dir": has_dir,
        "has_spec": has_spec,
        "has_plan": has_plan,
        "has_state": has_state,
        "has_summaries": has_summaries,
        "git_dirty": git_dirty,
    }


@mcp.tool()
def dirigent_show_plan() -> str:
    """Render the current PLAN.json as a compact text summary.

    Equivalent to /dirigent:show-plan but available as an MCP tool the agent
    can call directly without going through a slash command.
    """
    plan = _read_json_safe(_dirigent_dir() / "PLAN.json")
    if plan is None:
        return "(no PLAN.json — run /dirigent:create-plan first)"

    lines = [f"# {plan.get('title', '(untitled plan)')}"]
    if summary := plan.get("summary"):
        lines.append("")
        lines.append(summary)

    phases = plan.get("phases", [])
    for phase in phases:
        lines.append("")
        lines.append(f"## Phase {phase.get('id', '?')}: {phase.get('name', '')}")
        for task in phase.get("tasks", []):
            tid = task.get("id", "?")
            tname = task.get("name", "")
            tmodel = task.get("model", "")
            tag = f" [{tmodel}]" if tmodel else ""
            lines.append(f"  - {tid}: {tname}{tag}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
