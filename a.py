import asyncio
import os
import sys
from typing import Literal

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from claude_agent_sdk.types import SystemPromptPreset
from pydantic import BaseModel, Field

IOS_PROJECT = "/Users/jk/projects/fmv-mobile-app/ios"


# ── Models ─────────────────────────────────────────────────────────────────────

class AIReadinessScore(BaseModel):
    score: int = Field(..., ge=0, le=10, description="AI readiness score 0–10.")
    reason: str = Field(
        ...,
        description=(
            "Cite at least three specific filenames or patterns observed. "
            "For each of the five axes (test coverage, type safety, modularity, "
            "documentation, CI/CD signals) state briefly what you found."
        ),
    )


class GreenfieldScaffoldingStep(BaseModel):
    step_command: str = Field(
        ...,
        description=(
            "Exact shell command or concise manual instruction. "
            "For bash_script steps use the real CLI invocation, not pseudocode."
        ),
    )
    step_type: Literal["manual", "bash_script"] = Field(
        ..., description="Prefer bash_script. Use manual only for inherently human steps."
    )
    reason: str = Field(..., description="One sentence: why this step is necessary.")
    step_check_command: str = Field(
        ...,
        description=(
            "Shell command that exits 0 on success and non-zero on failure. "
            "Must be different from step_command. No placeholders."
        ),
    )


class GreenfieldScaffolding(BaseModel):
    steps: list[GreenfieldScaffoldingStep] = Field(
        ..., description="Ordered scaffold steps; each can assume all prior steps succeeded."
    )
    e2e_testability_covered: bool
    unit_testability_covered: bool
    integration_testability_covered: bool
    static_analysis_covered: bool
    frameworks: list[str] = Field(..., description="Libraries/frameworks introduced by these steps.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _print_scaffold(scaffold: GreenfieldScaffolding, technology: str) -> None:
    W = 72
    CHECK, CROSS = "\u2713", "\u2717"
    DASH = "\u2014"

    print(f"\n{'═' * W}")
    print(f"  GREENFIELD SCAFFOLD \u2014 rewrite \u2192 {technology}")
    fw = ', '.join(scaffold.frameworks) or DASH
    print(f"  {len(scaffold.steps)} steps  |  frameworks: {fw}")
    print(f"{'═' * W}\n")

    for i, step in enumerate(scaffold.steps, 1):
        badge = "bash  " if step.step_type == "bash_script" else "manual"
        print(f"  [{i:02d}] [{badge}]  {step.step_command}")
        print(f"          why    \u2192 {step.reason}")
        print(f"          verify \u2192 {step.step_check_command}")
        print()

    print(f"  {'─' * (W - 2)}")
    print("  Testability coverage")
    for label, ok in [
        ("E2E         ", scaffold.e2e_testability_covered),
        ("Integration ", scaffold.integration_testability_covered),
        ("Unit        ", scaffold.unit_testability_covered),
        ("Static anal.", scaffold.static_analysis_covered),
    ]:
        print(f"    {label}  {CHECK if ok else CROSS}")
    print(f"{'═' * W}")


def _emit_scaffold_script(scaffold: GreenfieldScaffolding, path: str = "scaffold.sh") -> None:
    lines = [
        "#!/usr/bin/env bash",
        "# Auto-generated scaffold — review before running.",
        "set -euo pipefail",
        "",
    ]
    for i, step in enumerate(scaffold.steps, 1):
        lines += [
            f"# ── Step {i}: {step.reason} ──",
            step.step_command,
            f"# verify: {step.step_check_command}",
            step.step_check_command,
            "",
        ]
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    os.chmod(path, 0o755)
    print(f"\n  scaffold script \u2192 {path}")


# ── Tasks ──────────────────────────────────────────────────────────────────────

async def ai_readiness() -> None:
    async for message in query(
        prompt=(
            "Assess the AI readiness of this iOS project and return a score from 0 to 10.\n\n"
            "AI Readiness measures how well-suited a codebase is for autonomous AI-assisted "
            "development. Evaluate across these five axes, weighted equally:\n"
            "  1. Test coverage — unit, integration, and/or UI tests present and meaningful?\n"
            "  2. Type safety — types declared consistently (Swift types, nullability annotations)?\n"
            "  3. Modularity — concerns separated into small, focused files/modules?\n"
            "  4. Documentation — public APIs and non-obvious logic commented?\n"
            "  5. CI/CD signals — Fastfile, Makefile, or similar automation the AI can invoke?\n\n"
            "Read at least five representative source files spanning different layers "
            "(UI, networking, data, tests) before scoring. "
            "Your `reason` must name specific files and state what you found for each axis."
        ),
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Bash"],
            cwd=IOS_PROJECT,
            model="claude-haiku-4-5",
            setting_sources=["project"],
            output_format={
                "type": "json_schema",
                "schema": AIReadinessScore.model_json_schema(),
            },
        ),
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            score = AIReadinessScore.model_validate(message.structured_output)
            print(f"Score: {score.score}/10")
            print(f"Reason:\n{score.reason}")
            if message.model_usage and "costUSD" in message.model_usage:
                print(f"Cost: ${message.model_usage['costUSD']:.4f}")


async def greenfield_scaffold(technology: str) -> None:
    async for message in query(
        prompt=(
            "Analyse this project, then produce a greenfield scaffold plan to rewrite it "
            "in the target technology (see system prompt).\n\n"
            "Before planning:\n"
            "  - Read representative source files to map screens, navigation, and the data/network layer.\n"
            "  - Use the context7 MCP server to fetch current docs for every library you recommend; "
            "do not rely on training-time knowledge for version numbers or API details.\n\n"
            "Rules for every step:\n"
            "  - Prefer official bootstrapping CLIs over heredoc file writes.\n"
            "  - Every bash_script step must be idempotent (guard with existence checks).\n"
            "  - step_check_command must exit non-zero on failure and differ from step_command.\n"
            "  - Cover all test layers: unit, integration, E2E, and linting/static analysis.\n"
            "  - Order steps so each can assume all prior steps succeeded.\n"
            "  - Do not include any step that modifies the existing source."
        ),
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Bash", "mcp__context7__*"],
            cwd=IOS_PROJECT,
            model="claude-sonnet-4-5",
            setting_sources=["project"],
            system_prompt=SystemPromptPreset(type="preset", preset="claude_code", append=f"Target technology for the rewrite: {technology}."),
            mcp_servers={
                "context7": {"type": "http", "url": "https://mcp.context7.com/mcp"}
            },
            output_format={
                "type": "json_schema",
                "schema": GreenfieldScaffolding.model_json_schema(),
            },
        ),
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            scaffold = GreenfieldScaffolding.model_validate(message.structured_output)
            _print_scaffold(scaffold, technology)
            _emit_scaffold_script(scaffold)
            if message.model_usage and "costUSD" in message.model_usage:
                print(f"Cost: ${message.model_usage['costUSD']:.4f}")


if __name__ == "__main__":
    technology = sys.argv[1] if len(sys.argv) > 1 else "React Native"
    asyncio.run(greenfield_scaffold(technology))
