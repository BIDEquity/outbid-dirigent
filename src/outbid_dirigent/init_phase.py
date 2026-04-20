"""
Init phase — bootstraps dev environment before planning.

The init phase:
1. Runs .outbid/init.sh or init.sh to start services, seed data, set up auth
2. Generates ARCHITECTURE.md if it doesn't exist (via Claude Code agent)
3. Generates test-harness.json from ARCHITECTURE.md (via structured output)

If no init script exists, ARCHITECTURE.md is still generated and the harness
is derived from it. The harness contains only deterministic commands (build,
test, e2e, seed, dev) — no hallucinated curl or health check commands.
"""

import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from claude_agent_sdk import query as sdk_query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage
from loguru import logger

from outbid_dirigent.test_harness_schema import TestHarness
from outbid_dirigent.utils import strict_json_schema


class InitPhase:
    """Handles the pre-planning init phase."""

    INIT_TIMEOUT = 300  # 5 minutes
    INIT_SCRIPT_LOCATIONS = [
        ".outbid/init.sh",
        "init.sh",
    ]

    def __init__(self, repo_path: Path, runner=None, dirigent_dir: Optional[Path] = None):
        self.repo_path = repo_path
        self.runner = runner
        self.dirigent_dir = dirigent_dir or (repo_path / ".dirigent")
        self.dirigent_dir.mkdir(parents=True, exist_ok=True)

    def discover_init_script(self) -> Optional[Path]:
        """Find the init script in the repo."""
        for location in self.INIT_SCRIPT_LOCATIONS:
            script = self.repo_path / location
            if script.exists():
                logger.info(f"Found init script: {script}")
                return script
        return None

    def run_init_script(self, script_path: Path) -> dict:
        """Execute the init script and return results."""
        result = {
            "script": str(script_path.relative_to(self.repo_path)),
            "success": False,
            "output": "",
            "error": "",
            "duration_seconds": 0,
            "produced_harness": False,
        }

        start = datetime.now()
        proc = None

        try:
            script_path.chmod(0o755)

            proc = subprocess.run(
                ["bash", "-c", f'set -e; source "{script_path}" 2>&1'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=self.INIT_TIMEOUT,
            )

            result["output"] = proc.stdout[:10000]
            result["error"] = proc.stderr[:5000]
            result["success"] = proc.returncode == 0

            if proc.returncode != 0:
                logger.warning(f"Init script exited with code {proc.returncode}")

        except subprocess.TimeoutExpired:
            result["error"] = f"Init script timed out after {self.INIT_TIMEOUT}s"
            logger.error(result["error"])
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Init script error: {e}")

        result["duration_seconds"] = (datetime.now() - start).total_seconds()

        # Check if the script produced the harness itself
        harness_path = self.dirigent_dir / "test-harness.json"
        if harness_path.exists():
            harness = TestHarness.load(harness_path)
            if harness:
                result["produced_harness"] = True
                logger.info("Init script produced test-harness.json directly")

        return result

    # ══════════════════════════════════════════
    # MAIN ENTRY POINT
    # ══════════════════════════════════════════

    def run(self) -> bool:
        """Run the complete init phase.

        Flow:
        1. Discover and run init script (if exists)
        2. If init script produced test-harness.json → use it
        3. Generate ARCHITECTURE.md if it doesn't exist
        4. Generate test-harness.json from ARCHITECTURE.md via structured output

        Returns True always (non-blocking — best effort).
        """
        logger.info("Starting init phase...")

        script = self.discover_init_script()
        harness_path = self.dirigent_dir / "test-harness.json"

        # Step 1: Run init script if it exists
        if script:
            logger.info(f"Running init script: {script}")
            init_result = self.run_init_script(script)

            if not init_result["success"]:
                logger.warning("Init script failed (continuing — non-blocking)")
        else:
            logger.info("No init script found (.outbid/init.sh or init.sh)")

        # Step 2: Check if the script produced the harness
        harness = TestHarness.load(harness_path)

        # Step 3: Generate ARCHITECTURE.md if it doesn't exist
        arch_path = self.repo_path / "ARCHITECTURE.md"
        if not arch_path.exists() and self.runner:
            logger.info("No ARCHITECTURE.md found — generating one")
            self.runner._run_claude("Run /dirigent:generate-architecture", timeout=600)
        elif arch_path.exists():
            logger.info("ARCHITECTURE.md exists — skipping generation")

        # Step 4: Generate test-harness.json from ARCHITECTURE.md
        if harness is None and arch_path.exists():
            logger.info("Generating test-harness.json from ARCHITECTURE.md...")
            harness = generate_harness_from_architecture(arch_path, harness_path)

        if harness is None:
            logger.warning("No test harness produced — reviewer will only do static analysis")
        else:
            cmds = ", ".join(harness.commands.keys())
            logger.info(f"Test harness: commands=[{cmds}]")

        return True


# ══════════════════════════════════════════
# HARNESS GENERATION FROM ARCHITECTURE.MD
# ══════════════════════════════════════════

HARNESS_SYSTEM_PROMPT = """\
You extract a structured test harness from an ARCHITECTURE.md file.

The harness contains ONLY deterministic, runnable commands found in the architecture doc.
Do NOT invent commands — only extract what is documented.

## Rules
- commands.build: the build command from the Development Workflow or Testing section
- commands.test: the test command (unit tests)
- commands.e2e: the e2e test command (if documented)
- commands.seed: the seed/data command (if documented)
- commands.dev: the dev server command
- Omit command keys that aren't documented
- env_vars: extract from the Configuration section
- portal: extract dev server command and port from Development Workflow
- _sources: for each value, cite the ARCHITECTURE.md section where you found it
- notes: anything important that doesn't fit the schema
"""


def generate_harness_from_architecture(
    arch_path: Path,
    harness_path: Path,
    model: str = "claude-haiku-4-5",
) -> Optional[TestHarness]:
    """Generate test-harness.json from ARCHITECTURE.md via structured output.

    Reads the architecture doc and extracts commands, env vars, and portal config
    into a strict TestHarness schema. The LLM fills fields but cannot invent new ones.
    """
    arch_content = arch_path.read_text(encoding="utf-8")
    if not arch_content.strip():
        logger.warning("ARCHITECTURE.md is empty — cannot generate harness")
        return None

    user_prompt = (
        f"<architecture>\n{arch_content}\n</architecture>\n\n"
        f"Extract the test harness from this architecture document."
    )

    try:
        start = datetime.now()
        structured, usage = asyncio.run(_aquery_harness(user_prompt, model))
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)

        if structured is None:
            logger.error("Harness generation: no structured output returned")
            return None

        try:
            harness = TestHarness.model_validate(structured)
        except Exception as e:
            logger.error(f"Harness generation: failed to parse output: {e}")
            return None

        try:
            from outbid_dirigent.logger import get_logger

            dlogger = get_logger()
            input_tokens = int(usage.get("input_tokens", 0) or 0)
            output_tokens = int(usage.get("output_tokens", 0) or 0)
            dlogger.api_usage(
                component="harness_generator",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=int(usage.get("cache_read_input_tokens", 0) or 0),
                cache_write_tokens=int(usage.get("cache_creation_input_tokens", 0) or 0),
                cost_cents=int((input_tokens * 1 + output_tokens * 5) / 10000),
                operation="generate_harness",
                duration_ms=duration_ms,
            )
        except RuntimeError:
            pass  # Logger not initialized (e.g. standalone call)

        harness.save(harness_path)
        logger.info(f"Test harness generated from ARCHITECTURE.md ({duration_ms}ms)")
        return harness

    except Exception as e:
        logger.error(f"Harness generation error: {e}")
        return None


async def _aquery_harness(user_prompt: str, model: str) -> tuple[Optional[dict], dict]:
    """Run harness extraction via claude_agent_sdk. Returns (structured_output, usage).

    Drains the generator to completion before returning — see the matching
    comment in llm_router._aquery_route for the subprocess-cleanup reason.
    """
    options = ClaudeAgentOptions(
        model=model,
        allowed_tools=[],
        permission_mode="bypassPermissions",
        setting_sources=[],  # don't load user/project/local settings; minimal context
        system_prompt=HARNESS_SYSTEM_PROMPT,
        output_format={
            "type": "json_schema",
            "schema": strict_json_schema(TestHarness.model_json_schema()),
        },
    )
    structured: Optional[dict] = None
    usage: dict = {}
    async for message in sdk_query(prompt=user_prompt, options=options):
        if isinstance(message, ResultMessage) and not message.is_error:
            structured = message.structured_output
            usage = message.usage or {}
    return structured, usage
