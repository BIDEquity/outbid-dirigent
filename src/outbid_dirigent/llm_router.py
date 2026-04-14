#!/usr/bin/env python3
"""
Outbid Dirigent – LLM Router
Routes specs to execution paths using Claude structured outputs.
Falls back to heuristic routing on API failure.
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import anthropic
from pydantic import BaseModel, Field

from outbid_dirigent.logger import get_logger
from outbid_dirigent.utils import strict_json_schema


class RouteChoice(str, Enum):
    QUICK = "quick"
    GREENFIELD = "greenfield"
    LEGACY = "legacy"
    HYBRID = "hybrid"
    TESTABILITY = "testability"
    TRACKING = "tracking"


class RouteDecision(BaseModel):
    """Structured output schema for the LLM route decision."""
    route: RouteChoice = Field(description="The execution route to take")
    justification: str = Field(description="2-3 sentences explaining why this route was chosen over the alternatives")
    confidence: str = Field(description="high, medium, or low")


ROUTE_SYSTEM_PROMPT = """\
You are a routing engine for a software development orchestrator called "Dirigent".
Your job is to pick the best execution route for a given spec (feature request / task description).

Available routes:

- **quick**: Tiny change, doable in a single planning+execution pass. No init, no test suite, no entropy cleanup. Use when the spec is very small and straightforward.
- **greenfield**: New project or major new module on a modern stack. Scaffolds architecture first, then plans and executes.
- **legacy**: Existing codebase with business rules that must be preserved. Extracts business rules before planning, verifies them after each task.
- **hybrid**: Feature work on an existing, actively maintained project. Quick-scans relevant files, plans with repo context.
- **testability**: The goal is to improve test infrastructure itself (add e2e framework, seed data, health checks, CI setup). Not for "add tests for feature X".
- **tracking**: The goal is to add product analytics / event tracking (PostHog, Mixpanel, etc.).

Decision guidelines:
- Prefer **quick** for specs under ~200 words that describe a single, contained change.
- Prefer **legacy** when the spec involves migration, refactoring across a large old codebase, or explicitly mentions preserving existing behavior.
- Prefer **greenfield** when the spec describes building something from scratch or the repo is brand new / nearly empty.
- Prefer **hybrid** as the default for feature work on an existing project.
- Only pick **testability** or **tracking** when the spec is specifically about those concerns, not when they're mentioned in passing.
"""


def determine_route_llm(
    spec_content: str,
    commit_count: int,
    test_harness_summary: Optional[str] = None,
    model: str = "claude-haiku-4-5",
    dirigent_dir: Optional[Path] = None,
) -> Optional[RouteDecision]:
    """
    Ask an LLM to pick the route using structured outputs.

    Args:
        spec_content: The full spec text.
        commit_count: Number of commits in the repo.
        test_harness_summary: Summary from test-harness.json if it exists.
        model: Model to use (haiku for speed/cost).
        dirigent_dir: Where to save the LLM routing decision.

    Returns:
        RouteDecision or None on failure.
    """
    logger = get_logger()

    # Build the user prompt with all non-ephemeral inputs
    user_parts = [f"<spec>\n{spec_content}\n</spec>"]
    user_parts.append(f"<repo-metadata>\nCommit count: {commit_count}\n</repo-metadata>")

    if test_harness_summary:
        user_parts.append(f"<test-harness>\n{test_harness_summary}\n</test-harness>")
    else:
        user_parts.append("<test-harness>No test harness configured.</test-harness>")

    user_parts.append("Pick the best route and justify your decision.")

    try:
        client = anthropic.Anthropic()
        start = datetime.now()

        response = client.messages.parse(
            model=model,
            max_tokens=500,
            system=ROUTE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n\n".join(user_parts)}],
            output_config={"format": {"type": "json_schema", "schema": strict_json_schema(RouteDecision.model_json_schema())}},
        )

        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        try:
            decision = RouteDecision.model_validate_json(response.content[0].text)
        except Exception as e:
            logger.error(f"LLM router: failed to parse route decision: {e}")
            return None

        # Log usage
        usage = response.usage
        logger.api_usage(
            component="llm_router",
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cost_cents=int((usage.input_tokens * 1 + usage.output_tokens * 5) / 10000),
            operation="route_decision",
            duration_ms=duration_ms,
        )

        logger.info(f"LLM route: {decision.route.value} ({decision.confidence}) — {decision.justification[:80]}")

        # Save decision for traceability
        if dirigent_dir:
            _save_llm_decision(dirigent_dir, decision, model, duration_ms)

        return decision

    except anthropic.APIError as e:
        logger.error(f"LLM router API error: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM router error: {e}")
        return None


def _save_llm_decision(dirigent_dir: Path, decision: RouteDecision, model: str, duration_ms: int):
    """Save the LLM routing decision for audit/debugging."""
    dirigent_dir.mkdir(parents=True, exist_ok=True)
    path = dirigent_dir / "LLM_ROUTE.json"
    data = {
        "route": decision.route.value,
        "justification": decision.justification,
        "confidence": decision.confidence,
        "model": model,
        "duration_ms": duration_ms,
        "decided_at": datetime.now().isoformat(),
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
