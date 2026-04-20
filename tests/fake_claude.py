#!/usr/bin/env python3
"""
Fake claude binary for deterministic E2E testing.

Acts as a drop-in replacement for the real `claude` CLI. Parses the same
args, detects which /dirigent: skill is being invoked, and writes the
appropriate output files + git commits.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────
# Arg parsing
# ─────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--dangerously-skip-permissions", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--effort", default=None)
    parser.add_argument("--append-system-prompt", default=None)
    parser.add_argument("--plugin-dir", action="append", default=[])
    parser.add_argument("-p", "--prompt", default="")
    args, _ = parser.parse_known_args()
    return args


# ─────────────────────────────────────────────────────────────
# Skill detection
# ─────────────────────────────────────────────────────────────

SKILLS = [
    "create-plan",
    "implement-task",
    "create-contract",
    "review-phase",
    "fix-review",
    "extract-business-rules",
    "quick-scan",
    "greenfield-scaffold",
]


def detect_skill(prompt: str) -> str:
    for skill in SKILLS:
        if f"/dirigent:{skill}" in prompt:
            return skill
    # Also detect agent-dispatch prompts: "Use the X agent to..."
    agent_to_skill = {
        "contract-negotiator": "create-contract",
        "reviewer": "review-phase",
        "implementer": "fix-review",
    }
    for agent_name, skill in agent_to_skill.items():
        if f"{agent_name} agent" in prompt:
            return skill
    return "unknown"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def dirigent_dir() -> Path:
    d = Path(os.getcwd()) / ".dirigent"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def git_commit(msg: str):
    subprocess.run(["git", "add", "-A"], cwd=os.getcwd(), check=False)
    subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=os.getcwd(),
        check=False,
        env={**os.environ, "GIT_AUTHOR_NAME": "fake-claude", "GIT_AUTHOR_EMAIL": "fake@claude.test",
             "GIT_COMMITTER_NAME": "fake-claude", "GIT_COMMITTER_EMAIL": "fake@claude.test"},
    )


# ─────────────────────────────────────────────────────────────
# Skill handlers
# ─────────────────────────────────────────────────────────────

def handle_create_plan(prompt: str):
    plan = {
        "title": "Test Feature",
        "summary": "E2E test",
        "phases": [
            {
                "id": "01",
                "name": "Core Implementation",
                "tasks": [
                    {
                        "id": "01-01",
                        "name": "Create main module",
                        "description": "Create core logic",
                        "files_to_create": ["src/feature.py"],
                        "files_to_modify": [],
                        "model": "sonnet",
                        "effort": "medium",
                    },
                    {
                        "id": "01-02",
                        "name": "Add tests",
                        "description": "Add tests for core module",
                        "files_to_create": ["tests/test_feature.py"],
                        "files_to_modify": [],
                        "model": "haiku",
                        "effort": "low",
                    },
                ],
            }
        ],
        "estimated_complexity": "low",
        "assumptions": ["Project uses pytest"],
        "out_of_scope": ["Deployment"],
    }
    out = dirigent_dir() / "PLAN.json"
    write_json(out, plan)
    print(f"fake-claude: wrote {out}")


def handle_execute_task(prompt: str):
    # Extract task id from <task id="..."> in prompt
    m = re.search(r'<task\s+id=["\']([^"\']+)["\']', prompt)
    task_id = m.group(1) if m else "00-00"

    # Create a simple source file
    safe_id = task_id.replace("-", "_")
    src_file = Path(os.getcwd()) / f"src/task_{safe_id}.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        f'"""Auto-generated stub for task {task_id}."""\n\n\ndef hello_{safe_id}():\n    return "hello from task {task_id}"\n',
        encoding="utf-8",
    )

    # Write summary
    summary_path = dirigent_dir() / "summaries" / f"{task_id}-SUMMARY.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        f"# Task {task_id} Summary\n\nCompleted by fake-claude.\n\n## Changes\n- Created `src/task_{safe_id}.py`\n",
        encoding="utf-8",
    )

    # git commit
    git_commit(f"feat: task {task_id}")
    print(f"fake-claude: executed task {task_id}")


def handle_create_contract(prompt: str):
    # Extract phase id — look for /dirigent:create-contract 01 or similar
    m = re.search(r"/dirigent:create-contract\s+(\S+)", prompt)
    if not m:
        # Fall back to any phase-id-like token
        m = re.search(r'phase[_\-\s]+id["\s:=]+["\']?(\w+)', prompt, re.IGNORECASE)
    phase_id = m.group(1) if m else "01"

    contract = {
        "phase_id": phase_id,
        "phase_name": f"Phase {phase_id}",
        "objective": f"Implement phase {phase_id} features",
        "acceptance_criteria": [
            {
                "id": f"AC-{phase_id}-01",
                "description": "All source files created without syntax errors",
                "verification": "Run: python -m py_compile src/*.py",
                "layer": "structural",
            },
            {
                "id": f"AC-{phase_id}-02",
                "description": "Core function returns expected value",
                "verification": f"Run: python -c \"from src.task_{phase_id.replace('-','_')}_01 import *; print('ok')\"",
                "layer": "user-journey",
            },
        ],
        "quality_gates": [
            "All new/modified files compile without errors",
            "No regressions in existing functionality",
            "Code follows project conventions",
        ],
        "out_of_scope": [],
        "expected_files": [],
    }
    out = dirigent_dir() / "contracts" / f"phase-{phase_id}.json"
    write_json(out, contract)
    print(f"fake-claude: wrote contract for phase {phase_id}")


def handle_review_phase(prompt: str):
    # Extract phase id
    m = re.search(r"/dirigent:review-phase\s+(\S+)", prompt)
    if not m:
        m = re.search(r'phase[_\-\s]+id["\s:=]+["\']?(\w+)', prompt, re.IGNORECASE)
    phase_id = m.group(1) if m else "01"

    review = {
        "phase_id": phase_id,
        "iteration": 1,
        "verdict": "pass",
        "confidence": "static",
        "infra_tier": "7_none",
        "tests_run": 0,
        "tests_skipped_infra": 0,
        "caveat": "Verified by fake-claude (static analysis only)",
        "criteria_results": [
            {
                "ac_id": f"AC-{phase_id}-01",
                "verdict": "pass",
                "notes": "Files exist and compile",
                "evidence": [
                    {
                        "command": "python -m py_compile src/*.py",
                        "exit_code": 0,
                        "stdout_snippet": "",
                        "stderr_snippet": "",
                    }
                ],
                "verification_tier": "7_none",
            },
            {
                "ac_id": f"AC-{phase_id}-02",
                "verdict": "pass",
                "notes": "Function callable",
                "evidence": [
                    {
                        "command": "python -c \"print('ok')\"",
                        "exit_code": 0,
                        "stdout_snippet": "ok",
                        "stderr_snippet": "",
                    }
                ],
                "verification_tier": "7_none",
            },
        ],
        "findings": [],
        "summary": f"Phase {phase_id} passed review (fake-claude, static only).",
    }
    out = dirigent_dir() / "reviews" / f"phase-{phase_id}.json"
    write_json(out, review)
    print(f"fake-claude: wrote review for phase {phase_id}")


def handle_fix_review(prompt: str):
    print("Fix applied")


def handle_extract_business_rules(prompt: str):
    out = dirigent_dir() / "BUSINESS_RULES.md"
    out.write_text(
        "# Business Rules\n\n- Rule 1: Always validate input\n- Rule 2: Return structured errors\n",
        encoding="utf-8",
    )
    print(f"fake-claude: wrote {out}")


def handle_quick_scan(prompt: str):
    out = dirigent_dir() / "CONTEXT.md"
    out.write_text(
        "# Project Context\n\nFake context generated by fake-claude for E2E testing.\n",
        encoding="utf-8",
    )
    print(f"fake-claude: wrote {out}")


def handle_greenfield_scaffold(prompt: str):
    """Simulate the greenfield scaffold step: ARCHITECTURE.md + start.sh + test-harness.json."""
    cwd = Path(os.getcwd())

    # Write ARCHITECTURE.md with the three sections
    arch = cwd / "ARCHITECTURE.md"
    arch.write_text("""\
# Architecture

<testing-verification>
## Testing & Verification

### Stack
Streamlit + DuckDB
Archetype: Dashboard for this data

### Test Suite
uv run pytest tests/ -v
Framework: pytest
Location: tests/

### Dev Server
uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
Port: 8501

### How to Verify Manually
1. Run `./start.sh`
2. Open http://localhost:8501
3. Verify the dashboard loads
</testing-verification>

<architecture-decisions>
## Architecture Decisions

### Stack Choice
Archetype: Dashboard for this data
Combo: Streamlit + DuckDB
Rationale: SPEC asks for a data dashboard — Streamlit is the default Python UI, DuckDB for analytics.

### Project Bootstrap
uv init --name app
uv add streamlit duckdb

### File Organization
```
app.py
tests/
  test_app.py
start.sh
```

### Decisions NOT Made
- Auth strategy (not needed per SPEC)
</architecture-decisions>

<key-patterns>
## Key Patterns

### Opinionated Defaults (non-negotiable)
- Package management: `uv` — not pip, not poetry
- DataFrames: `polars` — not pandas
- Validation / API I/O: `pydantic`
- Config: `pydantic-settings`
- Internal data objects: `dataclasses`
- HTTP client: `httpx` — not requests
- Logging: `loguru`
- Testing: plain `pytest` functions + fixtures — not unittest.TestCase
- Formatting: `ruff format`
- Abstractions: none until 2+ implementations
- Error handling: let it crash, validate at boundaries only

### Project Conventions
- Naming: snake_case for files and functions
- Config access: pydantic-settings from .env
</key-patterns>
""", encoding="utf-8")

    # Write start.sh
    start_sh = cwd / "start.sh"
    start_sh.write_text("""\
#!/bin/bash
set -e
cd "$(dirname "$0")"
uv sync
exec uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
""", encoding="utf-8")
    start_sh.chmod(0o755)

    # Write test-harness.json
    harness = {
        "commands": {
            "test": {
                "command": "uv run pytest tests/ -v",
                "explanation": "Run all unit tests with pytest",
            },
            "dev": {
                "command": "uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true",
                "explanation": "Start the Streamlit dev server",
            },
        },
        "env_vars": {},
        "portal": {
            "start_command": "uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true",
            "port": 8501,
            "url_after_start": "/",
        },
        "_sources": {
            "commands.test": "stacks/streamlit.md",
            "commands.dev": "stacks/streamlit.md",
            "portal.port": "stacks/streamlit.md",
        },
    }
    write_json(dirigent_dir() / "test-harness.json", harness)

    git_commit("docs: greenfield scaffold — Streamlit + DuckDB, testing strategy, start script")
    print("fake-claude: greenfield scaffold complete")


def handle_unknown(prompt: str):
    print("fake-claude: unknown skill — noop (success)")


# ─────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────

HANDLERS = {
    "create-plan": handle_create_plan,
    "implement-task": handle_execute_task,
    "create-contract": handle_create_contract,
    "review-phase": handle_review_phase,
    "fix-review": handle_fix_review,
    "extract-business-rules": handle_extract_business_rules,
    "quick-scan": handle_quick_scan,
    "greenfield-scaffold": handle_greenfield_scaffold,
    "unknown": handle_unknown,
}


def main():
    args = parse_args()
    skill = detect_skill(args.prompt)
    handler = HANDLERS.get(skill, handle_unknown)
    handler(args.prompt)
    sys.exit(0)


if __name__ == "__main__":
    main()
