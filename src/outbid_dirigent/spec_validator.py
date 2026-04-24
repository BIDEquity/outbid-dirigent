#!/usr/bin/env python3
"""
Outbid Dirigent – Spec Validator

Pre-execution gate. Runs after route selection, before spec compaction.
Decides whether the SPEC is suitable to drive a dirigent run for the chosen
route, and emits a structured list of obvious gaps that the user might want
to fill before running.

Hard rejects (`spec_ok=False`) abort the run. Soft gaps are logged and
persisted to `SPEC.validation.json` for the user to inspect.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage
from pydantic import BaseModel, Field

from outbid_dirigent.logger import get_logger
from outbid_dirigent.utils import strict_json_schema


# ---------------------------------------------------------------------------
# Pydantic schema
# ---------------------------------------------------------------------------

GapArea = Literal[
    "navigation",
    "authentication",
    "authorization",
    "data-persistence",
    "error-handling",
    "input-validation",
    "test-strategy",
    "deployment",
    "observability",
    "security",
    "accessibility",
    "other",
]
GapSeverity = Literal["blocker", "warn", "info"]
RejectionReason = Literal[
    "",
    "insufficient",
    "code-mismatch",
    "nsfw",
    "gambling",
    "illegal",
    "policy-violation",
    "other",
]


class SpecGap(BaseModel):
    area: GapArea
    severity: GapSeverity
    summary: str = Field(description="One-line description of what is missing")
    rationale: str = Field(description="Why this matters for the chosen route")
    suggested_addition: str = Field(
        description="Concrete sentence the user could add to the SPEC to close the gap"
    )


class SpecValidation(BaseModel):
    spec_ok: bool = Field(
        description="True if the spec is suitable to drive the dirigent run. False aborts."
    )
    spec_ok_rationale: str = Field(
        "",
        description="Empty when spec_ok=true. When false, explains the reason in 1-3 sentences.",
    )
    rejection_reason: RejectionReason = Field(
        "",
        description="Empty when spec_ok=true. Categorical reason when false.",
    )
    spec_gaps: list[SpecGap] = Field(
        default_factory=list,
        description="Soft gaps. Empty when the spec covers everything the route needs (or when the gaps are explicitly out of scope per the spec).",
    )


class SpecValidationError(Exception):
    """Raised when the validator rejects the spec. CLI catches this for clean exit."""

    def __init__(self, validation: SpecValidation):
        self.validation = validation
        super().__init__(validation.spec_ok_rationale or "Spec rejected by validator")


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

VALIDATOR_SYSTEM_PROMPT = """\
You are a spec validator for the Dirigent code-generation pipeline. Your job is
to decide, BEFORE any code is written, whether a SPEC.md is fit to drive an
autonomous run on the chosen route, and to surface obvious gaps the user might
want to address.

You receive: the SPEC text, the chosen route, and (when relevant) a brief
auto-gathered repo context (ARCHITECTURE.md, README.md, CLAUDE.md excerpts).

## Hard reject — set spec_ok=false

Reject the spec when it is:

1. **Content policy**: NSFW, gambling, malware, surveillance against people who
   have not consented, election manipulation, or other content that violates
   Anthropic's usage policies. Set rejection_reason to "nsfw", "gambling",
   "illegal", or "policy-violation" as appropriate.

2. **Insufficient**: only marketing prose, only a project name, no concrete
   testable requirements. The spec must give an autonomous coder enough to
   plan from. "Build me an app like Uber" without further detail is
   insufficient. Set rejection_reason="insufficient".

3. **Code-mismatch (HYBRID/LEGACY routes only)**: the spec demands behavior
   that directly contradicts what the existing codebase does and the spec
   does not acknowledge the contradiction. Example: spec says "use REST"
   but the codebase uses GraphQL throughout, with no migration plan named.
   Set rejection_reason="code-mismatch". Do NOT use this for GREENFIELD/QUICK.

When spec_ok=false, write spec_ok_rationale (1-3 sentences) explaining the
specific reason. Do not emit any spec_gaps for rejected specs — abort cleanly.

## Soft gaps — emit SpecGap entries

For each obvious omission relative to the chosen route, emit one SpecGap.
Apply two filters before emitting:

1. **Explicit non-decision filter**: if the spec explicitly excludes the area
   (e.g. "No authentication", "Out of Scope: deployment", "Internal tool,
   single user"), DO NOT emit a gap for that area. The user has decided.

2. **Route relevance filter**: only emit gaps that matter for the chosen
   route. See per-route triggers below.

## Per-route gap triggers

### GREENFIELD (building from scratch)
Common omissions:
- **navigation**: web app with no nav surface mentioned (no routes, no menu, no homepage flow)
- **authentication**: app talks about "users" but no auth approach mentioned (or explicit "no auth")
- **data-persistence**: stateful behavior described but no storage layer named
- **deployment**: production deployment story missing (acceptable for prototypes if SPEC says "local only")
- **test-strategy**: no e2e/unit testing approach named (greenfield-scaffold installs Playwright unconditionally, but spec should say what to test)

### HYBRID (extending an existing codebase)
- **integration**: spec doesn't say where the new feature plugs into existing code
- **data-persistence**: new entities mentioned without saying which DB / schema they extend

### LEGACY (rewriting/migrating)
- **test-strategy**: no behavioral parity strategy (how do we know the rewrite preserves behavior?)
- **data-persistence**: no migration / rollback plan for existing data

### QUICK (small change)
- Most gaps are acceptable. Only emit blockers.

### TESTABILITY (improving testability)
- **test-strategy**: spec should name which testability dimension (mocking, isolation, fixtures, …)

### TRACKING (adding analytics)
- **observability**: should name the analytics platform and the events to track

## Severity guide
- **blocker**: cannot generate working code without this. Use sparingly — most missing things become warns.
- **warn**: code will work but will be limited / different from what the user probably wanted
- **info**: nice-to-have, often inferred from defaults

## Hard rules

- Never invent gaps that don't apply. If the route is QUICK and the spec says
  "rename this function", emit zero gaps.
- Never emit a gap for an area the spec explicitly excludes.
- Never reject a spec for being short — short can still be sufficient
  ("Add a /health endpoint that returns {status: 'ok'}" is sufficient for a
  HYBRID route).
- The output is consumed by humans and downstream agents. Keep summaries
  one-line and rationales concrete.
"""


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def _gather_repo_context(repo_path: Path) -> str:
    """Collect well-known context files for the validator. Caps each at 5000 bytes."""
    parts: list[str] = []
    for filename, label in (
        ("ARCHITECTURE.md", "Architecture"),
        ("README.md", "README"),
        ("CLAUDE.md", "CLAUDE.md"),
        (".claude/CLAUDE.md", "CLAUDE.md (project)"),
    ):
        fp = repo_path / filename
        if fp.exists():
            content = fp.read_text(encoding="utf-8", errors="replace")[:5000]
            parts.append(f"### {label}\n\n{content}")
    return "\n\n---\n\n".join(parts)


def validate_spec(
    spec_content: str,
    route_type: str,
    repo_path: Path,
    dirigent_dir: Optional[Path] = None,
    model: str = "claude-sonnet-4-6",
) -> Optional[SpecValidation]:
    """Run the SPEC validator. Returns SpecValidation or None on API failure.

    Args:
        spec_content: Full markdown SPEC text.
        route_type: One of "quick", "greenfield", "hybrid", "legacy",
            "testability", "tracking".
        repo_path: Repo root for auto-gathering ARCHITECTURE.md / README.md / CLAUDE.md.
        dirigent_dir: Where to save SPEC.validation.json. If None, no file written.
        model: Model to use. Defaults to sonnet (matches spec_compactor default).

    Returns:
        SpecValidation on success. None on API/parse error (caller decides
        whether to treat that as a hard fail or a soft skip).
    """
    logger = get_logger()

    repo_context = _gather_repo_context(repo_path)
    user_prompt_parts = [
        f"<route>{route_type}</route>",
        f"<spec>\n{spec_content}\n</spec>",
    ]
    if repo_context:
        user_prompt_parts.append(f"<repo-context>\n{repo_context}\n</repo-context>")
    user_prompt_parts.append("\nValidate this spec for the chosen route.")
    user_prompt = "\n\n".join(user_prompt_parts)

    try:
        start = datetime.now()
        structured, usage = asyncio.run(_aquery_validate(user_prompt, model))
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        if structured is None:
            logger.error("Spec validator: model refused to produce a validation")
            return None

        try:
            validation = SpecValidation.model_validate(structured)
        except Exception as e:
            logger.error(f"Spec validator: failed to parse output: {e}")
            return None

        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        logger.api_usage(
            component="spec_validator",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
            cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
            cost_cents=int((input_tokens * 3 + output_tokens * 15) / 10000),
            operation="validate_spec",
            duration_ms=duration_ms,
        )

        if validation.spec_ok:
            logger.info(
                f"Spec validated for route={route_type}: "
                f"{len(validation.spec_gaps)} gap(s) flagged"
            )
        else:
            logger.warn(
                f"Spec REJECTED for route={route_type}: "
                f"{validation.rejection_reason} — {validation.spec_ok_rationale}"
            )

        if dirigent_dir is not None:
            _save_validation(dirigent_dir, validation)

        return validation

    except Exception as e:
        logger.error(f"Spec validator error: {e}")
        return None


async def _aquery_validate(user_prompt: str, model: str) -> tuple[Optional[dict], dict]:
    """Run validation via claude_agent_sdk. Returns (structured_output, usage)."""
    options = ClaudeAgentOptions(
        model=model,
        allowed_tools=[],
        permission_mode="bypassPermissions",
        setting_sources=[],
        system_prompt=VALIDATOR_SYSTEM_PROMPT,
        output_format={
            "type": "json_schema",
            "schema": strict_json_schema(SpecValidation.model_json_schema()),
        },
    )
    structured: Optional[dict] = None
    usage: dict = {}
    async for message in sdk_query(prompt=user_prompt, options=options):
        if isinstance(message, ResultMessage) and not message.is_error:
            structured = message.structured_output
            usage = message.usage or {}
    return structured, usage


def _save_validation(dirigent_dir: Path, validation: SpecValidation) -> None:
    """Persist SpecValidation to $DIRIGENT_RUN_DIR/SPEC.validation.json."""
    dirigent_dir.mkdir(parents=True, exist_ok=True)
    path = dirigent_dir / "SPEC.validation.json"
    path.write_text(validation.model_dump_json(indent=2), encoding="utf-8")
