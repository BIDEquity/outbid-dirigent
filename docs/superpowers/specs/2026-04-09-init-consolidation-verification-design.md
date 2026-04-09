# INIT Consolidation & Verification Strategy

## Problem

The INIT phase produces 7+ files to describe one thing: "what is this repo and how do you work with it." Three files are dead (never read downstream), three overlap heavily, and the test-harness.json `health_checks` / `verification_commands` are LLM-hallucinated and fail in ~90% of runs — causing the review loop to burn iterations on unfixable criteria.

### Current State

| File | Purpose | Consumer | Status |
|------|---------|----------|--------|
| `ARCHITECTURE.md` | Repo structure, tech stack, patterns | Planner, Tasks (LLM) | Keep, consolidate into |
| `CONVENTIONS.md` | Code patterns for LLM tasks | Tasks (LLM only) | **Eliminate** → absorb into ARCHITECTURE.md |
| `test-harness.json` | Verification commands, auth, health checks | Python + LLMs | **Replace** with strict schema |
| `infra-context.json` | Infra tier detection | Python | **Eliminate** — only served hallucinated verification |
| `testing-strategy.md` | Greenfield test approach | Tasks (LLM) | **Eliminate** → absorb into ARCHITECTURE.md |
| `architecture-decisions.md` | Greenfield arch decisions | Tasks (LLM) | **Eliminate** → absorb into ARCHITECTURE.md |
| `init-exports.env` | ENV dump after init script | **Nobody** | **Delete** (dead) |
| `init-output.log` | Init script stdout/stderr | **Nobody** | **Delete** (dead) |
| `init-new-env.json` | ENV diff after init script | **Nobody** | **Delete** (dead) |

### Root Causes

1. **No single source of truth** — 6 files describe the same repo from different angles
2. **Hallucinated verification** — LLM generates `curl` commands that require running services, env vars, and seed data that don't exist
3. **Free-form LLM output** — Skills write markdown/JSON freely, no schema enforcement, LLM invents sections
4. **No traceability** — Claims in generated docs can't be traced back to source code

## Solution

Two outputs from INIT, each with a clear purpose:

1. **ARCHITECTURE.md** — Human+LLM readable, structured markdown with XML tags per section. One file replaces ARCHITECTURE.md + CONVENTIONS.md + testing-strategy.md + architecture-decisions.md.

2. **test-harness.json** — Machine-readable, strict Pydantic schema. Generated via Pydantic AI / Claude Agent SDK with structured output (not free-form LLM writing). Contains only deterministic commands and env var metadata.

## Design

### ARCHITECTURE.md — Structured Markdown with XML Tags

Fixed sections, fixed order. The LLM fills in content but cannot invent sections. XML tags enable selective extraction by downstream consumers (e.g., task_runner extracts only `<key-patterns>`).

```markdown
# {Project Name} — Architecture

<system-overview>
> {One sentence: what this system does and for whom}

{Mermaid diagram: 5-10 boxes max}
</system-overview>

<testing-verification>
## Testing & Verification

### Build
{build command}                [source: package.json:X]

### Test Suite
{test command}                 [source: package.json:X]
{explanation of what tests cover and what they don't}

### E2E Tests (if applicable)
{e2e command}                  [source: playwright.config.ts:X]
{requirements: running server, seed data, etc.}

### Dev Server
{dev command}                  [source: package.json:X]
Port: {port}                   [source: .env:X]

### How to Verify Manually
1. {step-by-step instructions}
</testing-verification>

<tech-stack>
## Tech Stack

| Layer | Technology | Source |
|-------|-----------|--------|
| Language | {e.g. TypeScript 5.x} | `package.json:3` |
| Framework | {e.g. Next.js 14} | `package.json:5` |
| Database | {e.g. PostgreSQL via Prisma} | `prisma/schema.prisma:1` |
| Auth | {e.g. NextAuth.js} | `src/auth.config.ts:1` |
| Testing | {e.g. Vitest + Playwright} | `package.json:12` |
| Package Manager | {e.g. pnpm} | `pnpm-lock.yaml` |
</tech-stack>

<directory-structure>
## Directory Structure

{Top 2 levels with purpose annotations}
</directory-structure>

<entry-points>
## Entry Points

| Trigger | Code | Purpose |
|---------|------|---------|
| `POST /api/auth/login` | `src/app/api/auth/login/route.ts:14` | Password login |
| CLI: `npm run seed` | `scripts/seed.ts:1` | Populate dev database |
</entry-points>

<key-patterns>
## Key Patterns

{3-5 patterns with concrete source references. Replaces CONVENTIONS.md.}

- {Pattern name}: {description} [source: file:line]
- {Pattern name}: {description} [source: file:line]
</key-patterns>

<api-surface>
## API Surface

| Route Group | Purpose | Auth | Source |
|-------------|---------|------|--------|
| `/api/auth/*` | Authentication | Public | `src/app/api/auth/` |
| `/api/users/*` | User management | Admin | `src/app/api/users/` |
</api-surface>

<configuration>
## Configuration

| Variable | Purpose | Required | Source |
|----------|---------|----------|--------|
| `DATABASE_URL` | PostgreSQL connection | Yes | `src/lib/db.ts:5` |
</configuration>

<architecture-decisions>
## Architecture Decisions

{Replaces architecture-decisions.md. Only for greenfield/scaffold decisions.}

- {Decision}: {rationale} [source: file:line]
</architecture-decisions>

<development-workflow>
## Development Workflow

```bash
# Setup
{exact commands}

# Run
{exact commands}

# Test
{exact commands}
```
</development-workflow>
```

**Rules:**
- Every factual claim must cite `[source: file:line]`
- Sections are fixed — LLM cannot add or remove sections
- XML tags are mandatory for every section
- Structural sections (tech-stack, directory-structure) MUST NEVER be omitted
- Content sections (architecture-decisions) may be empty with a note: "No scaffold decisions — existing project"

### test-harness.json — Strict Pydantic Schema

Generated via **Pydantic AI structured output** (not free-form Claude CLI skill). The LLM receives repo context (package.json, pyproject.toml, .env.example, Dockerfile) and few-shot examples, then fills the schema. It cannot invent fields.

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class CommandSpec(BaseModel):
    """A single executable command with explanation of what it does and its boundaries."""
    command: str = Field(..., description="Exact runnable command (e.g. 'npm run build')")
    explanation: str = Field(..., description="What this does, what it covers, what it does NOT cover")


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
    password_env_var: str = Field("", description="Env var name containing password — never the value")


class PortalConfig(BaseModel):
    """Info the Outbid portal needs to show a live preview."""
    start_command: str = Field(..., description="Command to start dev server")
    port: int = Field(..., description="Port the dev server listens on")
    url_after_start: str = Field("/", description="Path to open after server starts")
    demo_login: DemoLogin = Field(default_factory=DemoLogin)


# Fixed command keys — LLM cannot invent new ones
COMMAND_KEYS = Literal["build", "test", "e2e", "seed", "dev"]


class TestHarness(BaseModel):
    """Strict test harness: only deterministic commands and env var metadata."""
    model_config = ConfigDict(populate_by_name=True)

    commands: dict[COMMAND_KEYS, CommandSpec] = Field(
        ..., description="Fixed set of commands. Omit keys that don't apply."
    )
    env_vars: dict[str, EnvVar] = Field(
        default_factory=dict, description="Environment variables the project requires"
    )
    portal: PortalConfig
    notes: str = Field("", description="Free text for anything not captured by the schema")
    sources: dict[str, str] = Field(
        default_factory=dict,
        alias="_sources",
        description="Citation map: field path → file:line where the value was found",
    )
```

**Generation approach:**
- Pydantic AI agent with `result_type=TestHarness`
- Input: file contents of package.json/pyproject.toml, .env.example, Dockerfile, relevant config files
- Few-shot examples for: Next.js project, Python FastAPI project, Go project
- The structured output constraint prevents the LLM from inventing fields or sections

**What is NOT in test-harness.json anymore:**
- `health_checks` — eliminated (hallucinated, never reliable)
- `verification_commands` — eliminated (hallucinated curl commands)
- `auth` — eliminated (login_command was hallucinated; demo_login covers the real need)
- `seed.users` — eliminated (seed_command in commands covers this)
- `testability_score` / `testability_rationale` / `testability_gaps` — eliminated (subjective LLM assessment, not actionable)
- `infra_tier` — eliminated (served hallucinated verification)
- `e2e_framework` — simplified to just the `e2e` command entry

### Eliminated Files

| File | Action | Reason |
|------|--------|--------|
| `CONVENTIONS.md` | Absorb into `<key-patterns>` | Only LLM-consumed, not a separate concern |
| `infra-context.json` | Delete schema + all references | Only served hallucinated verification pipeline |
| `testing-strategy.md` | Absorb into `<testing-verification>` | Same content, different file |
| `architecture-decisions.md` | Absorb into `<architecture-decisions>` | Same content, different file |
| `init-exports.env` | Delete write code | Dead — never read downstream |
| `init-output.log` | Delete write code | Dead — never read downstream |
| `init-new-env.json` | Delete write code + `_extract_env_diff()` | Dead — never read downstream |

### Verification Strategy Per Route

With the new ARCHITECTURE.md `<testing-verification>` section and strict test-harness.json:

**Greenfield:**
- GREENFIELD_SCAFFOLD must set up a test framework so `commands.test` is populated
- Contract-Negotiator adds structural criterion: `Run: {commands.build} && {commands.test}`
- No hallucinated curl — just the project's own build+test commands

**Legacy:**
- INIT reads existing test commands from package.json/pyproject.toml
- Contract-Negotiator adds regression criterion: `Run: {commands.test}`
- Existing tests must stay green

**Hybrid:**
- Same as Legacy + Planner is instructed to include test tasks for new features

**All routes:**
- Ship step sends `portal` config to Outbid portal for live preview
- PR body includes `<testing-verification>` section as "How to Verify"

### Downstream Consumer Changes

| Consumer | Currently reads | Will read |
|----------|----------------|-----------|
| `executor.py:run_tests()` | `harness.verification_commands` | `harness.commands["build"]`, `harness.commands["test"]` |
| `init_phase.py:wait_for_readiness()` | `harness.health_checks` | **Eliminated** — no more health check waiting |
| `task_runner.py` | CONVENTIONS.md, testing-strategy.md, architecture-decisions.md separately | `<key-patterns>`, `<testing-verification>`, `<architecture-decisions>` from ARCHITECTURE.md |
| `contract-negotiator` skill | test-harness.json (full) | `harness.commands["test"]` for structural criterion |
| `reviewer` skill | test-harness.json (full, runs health checks) | `harness.commands` for verification |
| `shipper.py` | `harness.verification_commands` | `harness.commands["build"]`, `harness.commands["test"]` |
| Ship step → Portal | N/A | `harness.portal` (start_command, port, url, demo_login) |

## Out of Scope

- Proteus/business rules integration (separate concern)
- INIT-Script support (`.outbid/init.sh`) — keep as-is, but remove dead env-capture code
- Route selection logic (analyzer.py) — unrelated
- Contract/Review schema changes (already done in prior commit)

## Success Criteria

1. INIT produces exactly 2 files: `ARCHITECTURE.md` + `test-harness.json`
2. test-harness.json is generated via Pydantic AI structured output, not free-form skill
3. `npm run build && npm test` (or equivalent) is the primary verification in every route
4. No more hallucinated curl commands in contracts or reviews
5. Portal receives `{ start_command, port, url_after_start, demo_login }` at ship time
6. All eliminated files are removed from generation code and downstream consumers
