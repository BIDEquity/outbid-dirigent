"""
Test harness schema — strict, deterministic specification for project verification.

Defines the commands, env vars, and portal config needed to build, test, and preview
a project. Generated via structured output (messages.parse) — the LLM fills fields
but cannot invent new ones.

Replaces the old free-form schema with hallucinated health_checks, verification_commands,
and auth configs that failed in ~90% of runs.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Fixed command keys — LLM cannot invent new ones
COMMAND_KEYS = Literal["build", "test", "e2e", "seed", "dev"]


class CommandSpec(BaseModel):
    """A single executable command with explanation of what it does and its boundaries."""
    command: str = Field(..., description="Exact runnable command (e.g. 'npm run build')")
    explanation: str = Field(
        ...,
        description="What this does, what it covers, what it does NOT cover",
    )


class EnvVar(BaseModel):
    """An environment variable required by the project."""
    source: Literal["doppler", "env", "hardcoded", "generated"] = Field(
        ..., description="Where this value comes from"
    )
    required: bool = True
    default: str = ""


class DemoLogin(BaseModel):
    """Credentials for demo/test access."""
    email: str = ""
    password_env_var: str = Field(
        "", description="Env var name containing password — never the value"
    )


class PortalConfig(BaseModel):
    """Info the Outbid portal needs to show a live preview."""
    start_command: str = Field(..., description="Command to start dev server")
    port: int = Field(..., description="Port the dev server listens on")
    url_after_start: str = Field("/", description="Path to open after server starts")
    demo_login: DemoLogin = Field(default_factory=DemoLogin)


class TestHarness(BaseModel):
    """
    Strict test harness: deterministic commands, env var metadata, and portal config.

    Generated via anthropic structured output (messages.parse) or from an init script.
    Lives at ${DIRIGENT_RUN_DIR}/test-harness.json.
    """
    model_config = ConfigDict(populate_by_name=True)

    commands: dict[COMMAND_KEYS, CommandSpec] = Field(
        ..., description="Fixed set of commands. Omit keys that don't apply."
    )
    env_vars: dict[str, EnvVar] = Field(
        default_factory=dict,
        description="Environment variables the project requires",
    )
    portal: PortalConfig
    notes: str = Field(
        "",
        description="Free text for anything not captured by the schema",
    )
    sources: dict[str, str] = Field(
        default_factory=dict,
        alias="_sources",
        description="Citation map: field path → file:line where the value was found",
    )

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            self.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: Path) -> Optional["TestHarness"]:
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def summary_for_prompt(self) -> str:
        """Compact summary for injection into LLM prompts."""
        lines = []
        for key, cmd in self.commands.items():
            lines.append(f"{key}: {cmd.command}")
            if cmd.explanation:
                lines.append(f"  ({cmd.explanation})")
        if self.env_vars:
            lines.append("Env vars:")
            for name, var in self.env_vars.items():
                req = "required" if var.required else "optional"
                lines.append(f"  {name}: {var.source}, {req}")
        if self.portal:
            lines.append(
                f"Dev server: {self.portal.start_command} → "
                f"localhost:{self.portal.port}{self.portal.url_after_start}"
            )
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)
