#!/usr/bin/env python3
"""
Outbid Dirigent – Final Review

Greenfield-only post-execution gate. The reviewer boots the prototype, smoke-
tests every SPEC requirement as a first-time user, and produces a structured
FinalReviewReport via SDK structured output.

Architecture choice — direct SDK call, NOT a plugin agent dispatch:
- The report schema is enforced by `output_format=json_schema` on the SDK
  call. The model cannot return malformed JSON.
- Tool surface is read-only (Bash, Read, Glob, Grep, playwright MCP). No
  Write/Edit so the reviewer cannot accidentally mutate the prototype.
- The fix loop on failure uses the existing implementer dispatch (open-
  ended, no structured output needed).
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    UserMessage,
)
from pydantic import BaseModel, Field, ValidationError

from outbid_dirigent.logger import get_logger
from outbid_dirigent.utils import strict_json_schema


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

ComponentType = Literal["backend", "frontend", "db", "cache", "other"]


class FinalReviewComponent(BaseModel):
    type: ComponentType
    port: Optional[int] = Field(
        None,
        description="Port the component listens on. None for components that do not bind a port.",
    )
    name: str = Field(description="Short human label, e.g. 'FastAPI app', 'Postgres'")
    is_main_entrypoint: bool = Field(
        False,
        description="True for the single component a user opens first. At most one component per report should be true.",
    )


class FinalReviewErrors(BaseModel):
    """All keys present always. Empty/false when the area was clean."""

    boot_failed: bool = False
    ports_unreachable: list[int] = Field(default_factory=list)
    spec_requirements_unmet: list[str] = Field(
        default_factory=list,
        description="SPEC requirement IDs (R1, R2, ...) that could not be exercised end-to-end.",
    )
    credentials_missing: bool = False
    other: list[str] = Field(
        default_factory=list,
        description="Free-text findings that don't fit the structured fields. One short sentence per entry.",
    )


class FinalReviewReport(BaseModel):
    passed: bool = Field(
        description="True iff every SPEC requirement traced to observable behavior AND no blocker hit during boot/navigation."
    )
    errors_occurred: FinalReviewErrors
    components: list[FinalReviewComponent] = Field(
        default_factory=list,
        description="Inventory enumerated when passed=true. Empty list when passed=false.",
    )

    def is_consistent(self) -> tuple[bool, str]:
        """Cheap structural sanity check on top of Pydantic validation.

        Returns (ok, reason). ok=True means the report's claims don't
        contradict each other.
        """
        if self.passed:
            if not self.components:
                return False, "passed=true requires at least one component"
            entries = sum(1 for c in self.components if c.is_main_entrypoint)
            if entries > 1:
                return False, f"only one component may be is_main_entrypoint=true (found {entries})"
            errs = self.errors_occurred
            if (
                errs.boot_failed
                or errs.ports_unreachable
                or errs.spec_requirements_unmet
                or errs.credentials_missing
                or errs.other
            ):
                return False, "passed=true contradicts non-empty errors_occurred"
        else:
            if self.components:
                return False, "passed=false requires components=[]"
        return True, ""


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

REVIEWER_SYSTEM_PROMPT = """\
You are a final-stage prototype reviewer. The build phase is complete. Your
job is to decide whether the prototype is fit to ship as a smoke-tested
deliverable, and to produce a structured FinalReviewReport.

# What you know

- The SPEC at `${DIRIGENT_RUN_DIR}/SPEC.md` — source of truth for required behavior.
- Repo conventions (CLAUDE.md, README.md, AGENTS.md if present).
- One hard convention: `./start.sh` at the repo root boots the application.

# What you do NOT know

- The implementation history. You did not write this code.
- Per-component internals. You read source only to identify entry points and ports.

# Your role

Act as a first-time user opening the prototype on a fresh machine. Validate
end-to-end behavior, not implementation correctness.

## Procedure (in this order, no skipping)

1. **Boot.** Run `./start.sh` in the background (e.g. `./start.sh > /tmp/start.log 2>&1 &`).
   Poll documented ports for up to 60 seconds before declaring boot failure.
   Use `curl --retry-connrefused --retry 12 --retry-delay 5` or a similar pattern.
   If `start.sh` does not exist, that is a finding — do NOT infer an alternative
   startup command.
2. **Locate test credentials** (in this order, stop when found):
   - `README.md` → `## Local Development` section
   - Dev-mode banner rendered in the running app
   - `.env.example` / `.env.local`
   - Seed migrations / fixtures in the backend stack
   If the app requires auth and no test credentials exist anywhere, set
   `errors_occurred.credentials_missing=true`.
3. **Smoke-test every SPEC requirement.** For each `Rn` in the SPEC's
   `## Requirements` section, attempt to exercise it as an end user would:
   - **UI:** navigate, click, complete the flow (use the playwright MCP tool)
   - **API:** hit the documented endpoint with the documented method (`curl`)
   - **CLI:** run the documented command with representative arguments
   Stop when every Rn traces to an observable behavior, OR when you've
   identified a blocker that prevents further testing.

# What is NOT your job

- Unit-testing components or reading source beyond entry-point identification
- Debugging or fixing failures (you have no Write tool, no Edit tool — report only)
- Refactoring suggestions, code style critiques, architectural advice
- Exhaustive edge-case coverage (this is a smoke test, not regression)

# Output

Your final response MUST be a FinalReviewReport. The schema is enforced —
the SDK will reject malformed JSON. Field rules:

- `passed`: `true` iff every SPEC requirement was observably exercised AND
  no blocker was hit during boot/navigation. Both conditions must hold.
- `errors_occurred`: every key always present. Empty list / `false` when
  the area was clean.
- `errors_occurred.spec_requirements_unmet`: list of SPEC requirement IDs
  (e.g. `["R3","R7"]`). Use the IDs verbatim from the SPEC, never paraphrase.
- `errors_occurred.other`: free-text findings that don't fit the structured
  fields. One short sentence per entry.
- `components`: enumerated when `passed=true` (this is the inventory the
  next phase consumes). Empty list when `passed=false`.
- `components[].type`: one of `backend, frontend, db, cache, other`.
- `components[].is_main_entrypoint`: at most one component may be `true` —
  the "front door" the user opens first.

# Hard rules

- One boot attempt. Boot failure is a finding, not a retry trigger.
- Be specific in error messages. "Login form POST /sign-in returns 500"
  beats "auth broken".
- Reference SPEC requirement IDs (R1, R2, ...) verbatim in
  `spec_requirements_unmet`.
- Do not edit code, do not commit. The orchestrator handles that.
- If `start.sh` does not exist, set `errors_occurred.boot_failed=true` and
  add `errors_occurred.other=["convention violation: start.sh missing at repo root"]`.
  Do not attempt an alternative startup command.
- Stop when you have enough evidence — either every Rn passed, or you
  found a blocker. Smoke test, not regression.
"""


# ---------------------------------------------------------------------------
# Reviewer driver
# ---------------------------------------------------------------------------


# Read-only tool surface. Mirrors task_runner's MCP whitelist patterns
# (mcp__plugin_playwright_playwright__* covers both install shapes).
_REVIEWER_ALLOWED_TOOLS = [
    "Read",
    "Bash",
    "Glob",
    "Grep",
    "mcp__playwright__*",
    "mcp__plugin_playwright_playwright__*",
]


def run_final_review(
    repo_path: Path,
    dirigent_dir: Path,
    model: str = "claude-sonnet-4-6",
    timeout_s: int = 600,
) -> Optional[FinalReviewReport]:
    """Run the final-review SDK call. Returns FinalReviewReport on success.

    Returns None when the SDK errored or the model failed to produce
    schema-conforming output. Caller treats None as a failed review and
    triggers the fix loop.

    Side effect: writes the report to `dirigent_dir/final-review.json` so
    the fix-loop agent can read it as input on the next round.
    """
    logger = get_logger()

    user_prompt = (
        "Boot the prototype, smoke-test every requirement in "
        "${DIRIGENT_RUN_DIR}/SPEC.md against the running app, and produce a "
        "FinalReviewReport. Follow the procedure in your system prompt exactly. "
        "Use playwright MCP for any UI interaction; use curl for API endpoints; "
        "run CLI commands directly via Bash."
    )

    try:
        start = datetime.now()
        structured, usage = asyncio.run(
            _aquery_review(user_prompt, model, repo_path, timeout_s)
        )
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        if structured is None:
            logger.error("Final review: SDK returned no structured output")
            return None

        try:
            report = FinalReviewReport.model_validate(structured)
        except ValidationError as e:
            logger.error(f"Final review: schema validation failed: {e}")
            return None

        ok, reason = report.is_consistent()
        if not ok:
            logger.error(f"Final review: report internally inconsistent — {reason}")
            return None

        # Cost telemetry — sonnet pricing (3/15 per M tokens)
        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        logger.api_usage(
            component="final_reviewer",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
            cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
            cost_cents=int((input_tokens * 3 + output_tokens * 15) / 10000),
            operation="final_review",
            duration_ms=duration_ms,
        )

        # Persist for the fix-loop agent (and for human inspection if failed)
        report_path = dirigent_dir / "final-review.json"
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        if report.passed:
            logger.info(
                f"Final review PASSED — {len(report.components)} component(s) "
                f"({duration_ms}ms)"
            )
        else:
            logger.warn(
                f"Final review FAILED — "
                f"{len(report.errors_occurred.spec_requirements_unmet)} unmet req(s), "
                f"boot_failed={report.errors_occurred.boot_failed}, "
                f"creds_missing={report.errors_occurred.credentials_missing} "
                f"({duration_ms}ms)"
            )

        return report

    except Exception as e:
        logger.error(f"Final review error: {e}")
        return None


async def _aquery_review(
    user_prompt: str,
    model: str,
    repo_path: Path,
    timeout_s: int,
) -> tuple[Optional[dict], dict]:
    """Run the reviewer via claude_agent_sdk. Returns (structured_output, usage).

    Loads the dirigent plugin so the playwright MCP tool is available, but
    constrains allowed_tools to a read-only subset (no Write, no Edit, no
    Agent). The model uses tools for boot + smoke-test, then produces a
    schema-conforming FinalReviewReport as its final result.
    """
    plugin_dir = Path(__file__).parent / "plugin"
    plugins: list[dict] = []
    if plugin_dir.exists():
        plugins.append({"type": "local", "path": str(plugin_dir)})

    options = ClaudeAgentOptions(
        model=model,
        cwd=str(repo_path),
        plugins=plugins,
        allowed_tools=_REVIEWER_ALLOWED_TOOLS,
        permission_mode="bypassPermissions",
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        output_format={
            "type": "json_schema",
            "schema": strict_json_schema(FinalReviewReport.model_json_schema()),
        },
    )

    structured: Optional[dict] = None
    usage: dict = {}
    logger = get_logger()

    async def _consume() -> None:
        nonlocal structured, usage
        async for message in sdk_query(prompt=user_prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        logger.debug(f"[final-review:text] {block.text[:500]}")
                    elif isinstance(block, ToolUseBlock):
                        logger.debug(
                            f"[final-review:tool] {block.name}({str(block.input)[:300]})"
                        )
            elif isinstance(message, UserMessage):
                # Tool results — surface what the reviewer actually saw
                logger.debug(f"[final-review:tool-result] {str(message.content)[:500]}")
            elif isinstance(message, ResultMessage) and not message.is_error:
                structured = message.structured_output
                usage = message.usage or {}

    try:
        await asyncio.wait_for(_consume(), timeout=timeout_s)
    except asyncio.TimeoutError:
        logger.error(f"Final review timed out after {timeout_s}s")
        return None, usage

    return structured, usage


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


def parse_review_report(path: Path) -> Optional[FinalReviewReport]:
    """Read a previously persisted report from disk. Used by the fix-loop
    agent's wrapper to read its input. Returns None on any failure.
    """
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        report = FinalReviewReport.model_validate(raw)
    except ValidationError:
        return None
    ok, _ = report.is_consistent()
    if not ok:
        return None
    return report


def commit_passing_report(
    repo_path: Path,
    run_dir: Path,
    round_n: int,
) -> tuple[bool, Optional[str]]:
    """Move final-review.json from run dir to repo root and commit it.

    Called only when the report passed. Failure here is non-fatal (logged
    by caller); the run continues to entropy-minimization regardless.

    Returns (success, commit_hash).
    """
    src = run_dir / "final-review.json"
    dst = repo_path / "final-review.json"
    if not src.exists():
        return False, None

    try:
        shutil.copyfile(src, dst)
    except OSError:
        return False, None

    try:
        subprocess.run(
            ["git", "add", "--", "final-review.json"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"chore(review): final review passed (round {round_n})"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return False, None

    try:
        sha = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return True, sha or None
    except subprocess.CalledProcessError:
        return True, None
