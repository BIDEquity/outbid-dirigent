"""
Test harness schema — what init.sh must produce for the reviewer.

The test harness tells the reviewer exactly how to verify features end-to-end:
- Where the running app is (base URL, port)
- How to authenticate (curl command, storageState, API token)
- What seed data exists (test users, sample records)
- What commands to run for e2e verification
- What health checks confirm the environment is alive

This is NOT a test manifest (that defines unit/integration test commands).
This IS a runtime verification spec: "here's a running system, here's how to poke it."
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    """How the reviewer can authenticate against the running app."""
    NONE = "none"                    # No auth needed (public endpoints)
    BEARER_TOKEN = "bearer_token"    # Static token from env var or init output
    COOKIE = "cookie"                # Login via curl, use cookie
    STORAGE_STATE = "storage_state"  # Playwright storageState.json
    BASIC_AUTH = "basic_auth"        # HTTP Basic Auth
    API_KEY = "api_key"              # API key in header


class AuthConfig(BaseModel):
    """How to authenticate for e2e testing."""
    method: AuthMethod = AuthMethod.NONE
    # For bearer_token / api_key: env var name containing the token (NEVER the value)
    token_env_var: str = ""
    # For cookie / bearer_token: a curl command that returns a token/session
    # e.g. "curl -s -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test\"}' | jq -r '.token'"
    login_command: str = ""
    # For storage_state: path to the Playwright storageState.json
    storage_state_path: str = ""
    # For basic_auth: env var names (NEVER values)
    username_env_var: str = ""
    password_env_var: str = ""


class SeedUser(BaseModel):
    """A test user seeded by init.sh."""
    role: str = Field(..., description="e.g. admin, user, viewer")
    email: str = ""
    # NEVER the actual password — either an env var name or a known test default
    password_env_var: str = ""
    password_default: str = Field("", description="Only for test-only defaults like 'test123'")
    notes: str = ""


class SeedData(BaseModel):
    """What data init.sh seeded into the system."""
    users: list[SeedUser] = Field(default_factory=list)
    description: str = Field("", description="What other data was seeded (records, fixtures, etc.)")
    seed_command: str = Field("", description="Command to re-run seeding if needed")


class HealthCheck(BaseModel):
    """A command to verify a service is alive."""
    name: str
    command: str = Field(..., description="Bash command that exits 0 when healthy")
    timeout_seconds: int = 30


class E2eCommand(BaseModel):
    """A command the reviewer can run for e2e verification."""
    name: str = Field(..., description="What this verifies")
    command: str = Field(..., description="Bash command to run")
    expected: str = Field("", description="What success looks like (exit 0, contains string, etc.)")


class E2eFrameworkConfig(BaseModel):
    """Configuration for a specific e2e framework (Playwright/Puppeteer/Cypress)."""
    framework: str = Field(..., description="playwright, puppeteer, cypress, or none")
    config_file: str = ""
    run_command: str = Field("", description="e.g. 'npx playwright test --project=chromium'")
    # If the framework has its own auth setup (Playwright globalSetup, etc.)
    has_global_setup: bool = False
    global_setup_file: str = ""


class TestHarness(BaseModel):
    """
    The test harness: everything the reviewer needs to verify features end-to-end.

    Produced by init.sh (or init phase), consumed by the reviewer.
    Lives at .dirigent/test-harness.json.
    """
    # Where is the app?
    base_url: str = Field(..., description="e.g. http://localhost:3000")
    port: int = 3000

    # How to authenticate?
    auth: AuthConfig = Field(default_factory=AuthConfig)

    # What seed data exists?
    seed: SeedData = Field(default_factory=SeedData)

    # Is everything running?
    health_checks: list[HealthCheck] = Field(default_factory=list)

    # What e2e framework is configured?
    e2e_framework: E2eFrameworkConfig = Field(
        default_factory=lambda: E2eFrameworkConfig(framework="none")
    )

    # Commands the reviewer can run to verify the feature works
    # These are the payoff — concrete, runnable verification steps
    verification_commands: list[E2eCommand] = Field(default_factory=list)

    # Services that init started (for context)
    services: list[str] = Field(default_factory=list, description="e.g. ['postgres', 'redis']")

    # ── Testability assessment ──

    testability_score: int = Field(
        0, ge=0, le=10,
        description="0-10 score: how well can the reviewer verify this project end-to-end?"
    )
    testability_rationale: str = Field(
        "",
        description="Why this score? What contributes to or detracts from testability?"
    )
    testability_description: str = Field(
        "",
        description="Plain-text description of the test setup: what works, what's available, "
                    "how the reviewer can verify features"
    )
    testability_gaps: list[str] = Field(
        default_factory=list,
        description="What's missing or broken — each gap is an actionable improvement"
    )

    # Overall status
    status: str = Field("ready", description="ready, partial, failed")
    notes: str = ""

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Optional["TestHarness"]:
        if not path.exists():
            return None
        try:
            return cls.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def json_template() -> str:
        return """{
  "base_url": "http://localhost:3000",
  "port": 3000,
  "auth": {
    "method": "bearer_token",
    "token_env_var": "",
    "login_command": "curl -s -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@test.com\",\"password\":\"test123\"}' | jq -r '.token'",
    "storage_state_path": "",
    "username_env_var": "",
    "password_env_var": ""
  },
  "seed": {
    "users": [
      {
        "role": "admin",
        "email": "admin@test.com",
        "password_env_var": "",
        "password_default": "test123",
        "notes": "Full access, seeded by init.sh"
      }
    ],
    "description": "10 sample products, 3 orders",
    "seed_command": "npm run db:seed"
  },
  "health_checks": [
    {
      "name": "App server",
      "command": "curl -sf http://localhost:3000/api/health",
      "timeout_seconds": 30
    },
    {
      "name": "Database",
      "command": "pg_isready -h localhost -p 5432",
      "timeout_seconds": 10
    }
  ],
  "e2e_framework": {
    "framework": "playwright",
    "config_file": "playwright.config.ts",
    "run_command": "npx playwright test --project=chromium",
    "has_global_setup": true,
    "global_setup_file": "e2e/global-setup.ts"
  },
  "verification_commands": [
    {
      "name": "API health",
      "command": "curl -sf http://localhost:3000/api/health",
      "expected": "exit 0, returns JSON with status ok"
    },
    {
      "name": "Auth flow",
      "command": "curl -s -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@test.com\",\"password\":\"test123\"}' -w '\\n%{http_code}'",
      "expected": "HTTP 200, response contains token"
    },
    {
      "name": "E2e test suite",
      "command": "npx playwright test --project=chromium",
      "expected": "exit 0, all tests pass"
    }
  ],
  "services": ["postgres", "redis"],
  "testability_score": 7,
  "testability_rationale": "Playwright configured with auth setup and seed data. Health checks pass. Missing: no API contract tests, no visual regression tests.",
  "testability_description": "Dev server runs on localhost:3000 with Postgres. Auth via bearer token from login endpoint. Test user seeded. Playwright e2e suite available. Reviewer can run curl commands for API verification and npx playwright test for UI flows.",
  "testability_gaps": [
    "No API contract/schema tests (e.g. OpenAPI validation)",
    "No visual regression testing configured",
    "Seed data is minimal — only 1 user, no edge-case data",
    "No load/performance test baseline"
  ],
  "status": "ready",
  "notes": ""
}"""

    def summary_for_reviewer(self) -> str:
        """Compact summary for the reviewer's prompt context."""
        lines = [
            f"Base URL: {self.base_url}",
            f"Auth: {self.auth.method.value}",
        ]
        if self.auth.login_command:
            lines.append(f"Login: {self.auth.login_command}")
        if self.auth.storage_state_path:
            lines.append(f"Storage state: {self.auth.storage_state_path}")
        if self.seed.users:
            for u in self.seed.users:
                pw = f"${u.password_env_var}" if u.password_env_var else u.password_default
                lines.append(f"Test user ({u.role}): {u.email} / {pw}")
        if self.health_checks:
            lines.append("Health checks:")
            for h in self.health_checks:
                lines.append(f"  - {h.name}: {h.command}")
        if self.verification_commands:
            lines.append("Verification commands:")
            for v in self.verification_commands:
                lines.append(f"  - {v.name}: {v.command}")
        if self.e2e_framework.framework != "none":
            lines.append(f"E2e: {self.e2e_framework.run_command}")
        if self.testability_score:
            lines.append(f"Testability: {self.testability_score}/10 — {self.testability_rationale}")
        if self.testability_gaps:
            lines.append("Gaps:")
            for g in self.testability_gaps:
                lines.append(f"  - {g}")
        return "\n".join(lines)
