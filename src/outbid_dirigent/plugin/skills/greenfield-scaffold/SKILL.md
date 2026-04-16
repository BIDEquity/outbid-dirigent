---
name: greenfield-scaffold
description: For greenfield projects, pick the opinionated stack, scaffold the project, and write architecture sections into ARCHITECTURE.md. Produces start.sh and test-harness.json.
context: fork
agent: infra-architect
---

# Greenfield Scaffold

You scaffold a greenfield project by picking an opinionated stack combo, running the scaffold commands, and writing the `<testing-verification>`, `<architecture-decisions>`, and `<key-patterns>` sections of ARCHITECTURE.md. You also produce `start.sh` and `test-harness.json`.

These artifacts guide every downstream step:
- **Planner** reads ARCHITECTURE.md sections to create tasks
- **Executor** reads `<key-patterns>` to constrain how the coding agent writes code
- **Test step** reads test-harness.json for build/test/e2e commands
- **Ship step** includes start.sh in the delivered repo and references it in the PR

Get them right and the entire feature ships clean. Get them wrong and every task fights the architecture.

## When This Runs

First step in the greenfield route (no init phase). You have:
- `${DIRIGENT_RUN_DIR}/SPEC.md` — what's being built
- `${DIRIGENT_RUN_DIR}/ANALYSIS.json` — repo structure, language, framework
- The live repo — read whatever you need

You create ARCHITECTURE.md from scratch (no prior generation step).

## Use context7 for Up-to-Date Docs

Before writing scaffold commands, config syntax, or framework-specific code, always query context7 for current documentation. Each stack file in `stacks/` has a "Docs" section showing the exact context7 calls to make.

```
1. mcp__context7__resolve-library-id  →  libraryName="<framework>"
2. mcp__context7__query-docs           →  libraryId=<result>, topic="<specific question>"
```

This is mandatory — your training data may be stale. Scaffold commands, config formats, and API surfaces change between versions.

## Step 1: Classify the SPEC

Read `${DIRIGENT_RUN_DIR}/SPEC.md` and match it to an archetype from `stacks/README.md`. Read the archetype combos table and pick the first one that fits.

**Do NOT deliberate over stack choices.** The stacks are opinionated defaults. Pick the combo, move on.

| SPEC Shape | Combo | Stack Files to Read |
|---|---|---|
| "Dashboard for this data" | Streamlit + DuckDB | `stacks/streamlit.md`, `stacks/duckdb.md` |
| "API + frontend app" | FastAPI + Vite+React | `stacks/fastapi.md`, `stacks/vite-react.md` |
| "Full-stack app with auth" (simple) | Next.js + PocketBase | `stacks/nextjs.md`, `stacks/pocketbase.md` |
| "Full-stack app with auth" (production) | Next.js + Supabase Local | `stacks/nextjs.md`, `stacks/supabase-local.md` |
| "App with database" | FastAPI + SQLite | `stacks/fastapi.md`, `stacks/sqlite.md` |
| "ML model demo" | Gradio | `stacks/gradio.md` |
| "Internal tool / form app" | Streamlit | `stacks/streamlit.md` |
| "Docs site / landing page" | Astro Starlight | `stacks/astro-starlight.md` |
| "Python app with real database" | FastAPI + Supabase Local | `stacks/fastapi.md`, `stacks/supabase-local.md` |
| "Data pipeline + dashboard" | Streamlit + DuckDB + FastAPI | `stacks/streamlit.md`, `stacks/duckdb.md`, `stacks/fastapi.md` |
| Default (unclear) | Streamlit | `stacks/streamlit.md` |

## Step 2: Verify Stack Availability

Read the stack files for your chosen combo. Run the "Check Installation" commands from each file. If a tool is missing, report it and stop — do not proceed with a broken stack.

```bash
# Example for Streamlit + DuckDB combo:
uv --version
python -c "import streamlit; print(streamlit.__version__)"
python -c "import duckdb; print(duckdb.__version__)"
```

## Step 3: Assess What Already Exists

Before scaffolding, check if the repo already has structure:

```bash
# Existing project files?
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null

# Existing test infrastructure?
ls jest.config* vitest.config* pytest.ini conftest.py 2>/dev/null
ls -d test/ tests/ __tests__/ 2>/dev/null

# Existing framework config?
ls next.config* vite.config* astro.config* 2>/dev/null
```

If `.brv/context-tree/` exists and `brv` CLI is available, query for existing architectural decisions:
```bash
brv query "What architecture patterns, testing strategies, and design decisions exist?"
```

**If the repo already has a framework config or package.json, skip scaffolding and work with what exists.**

## Step 4: Run Scaffold Commands

Read the "Scaffold" section of each stack file in your combo. Run the commands.

The scaffold commands are documented in each stack file under `stacks/`. Do NOT invent scaffold commands — use exactly what the stack file specifies.

**CRITICAL:** Never write framework config files manually (next.config.*, vite.config.*, etc.) — the scaffold generates version-correct configs.

## Step 5: Write ARCHITECTURE.md

Create ARCHITECTURE.md at the repo root. Write these three sections. The content comes from the stack files and the opinionated defaults in `stacks/README.md`.

### Section: `<testing-verification>`

```markdown
<testing-verification>
## Testing & Verification

### Stack
{combo name, e.g. "Streamlit + DuckDB"}
Archetype: {archetype name from Step 1}

### Build
{build command from stack file, if applicable}

### Test Suite
{test command from stack file}
Framework: {test framework from stack file}
Location: {test directory}

### Dev Server
{run command from stack file}
Port: {port from stack file}

### How to Verify Manually
1. {step-by-step for a human, using the run command from the stack file}
</testing-verification>
```

### Section: `<architecture-decisions>`

```markdown
<architecture-decisions>
## Architecture Decisions

### Stack Choice
Archetype: {archetype}
Combo: {list of stacks}
Rationale: {1-2 sentences why this combo fits the SPEC}

### Project Bootstrap
{scaffold commands from Step 4}

### File Organization
```
{proposed directory tree, 10-15 lines}
```

### Dependencies to Add
| Package | Purpose | Why this one |
|---------|---------|-------------|
| {pkg} | {what} | {why not alternatives} |

### Decisions NOT Made
{What's deliberately left open and why}
</architecture-decisions>
```

### Section: `<key-patterns>`

This section is critical — it flows into every task the executor runs. The coding agent reads it before writing any code. Include BOTH project-specific conventions AND the relevant opinionated defaults from `stacks/README.md`.

Read the "Opinionated Defaults" section of `stacks/README.md`. Copy the defaults that apply to the chosen stack. For a Python project, include the Python table. For a JS project, include the JS table. Always include the Architecture table.

```markdown
<key-patterns>
## Key Patterns

### Opinionated Defaults (non-negotiable)
{Copy the relevant rows from stacks/README.md "Opinionated Defaults" tables.
 For Python stacks: include the Python table.
 For JS stacks: include the JS table.
 Always include the Architecture table.
 Format as a flat list:}

- Package management: `uv` — not pip, not poetry
- DataFrames: `polars` — not pandas
- Validation / API I/O: `pydantic`
- Config: `pydantic-settings`
- Internal data objects: `dataclasses`
- HTTP client: `httpx` — not requests
- Logging: `loguru`
- Path handling: `pathlib.Path` — not os.path
- Testing: plain `pytest` functions + fixtures — not unittest.TestCase
- Formatting: `ruff format`
- Abstractions: none until 2+ implementations
- File nesting: max 2 levels deep
- Dependencies: fewer is better, don't add a lib for what stdlib does
- ORM: skip for prototypes, raw SQL or sqlmodel
- Auth: don't build it — PocketBase or Supabase handle it
- Error handling: let it crash, validate at boundaries only
- Don't add yet: no Dockerfile, no CI/CD, no monitoring, no i18n

### Project Conventions
- {Naming}: {convention} [source: scaffold or stack file]
- {Error handling}: {pattern}
- {Config access}: {pattern}
- {Exports}: {convention}
</key-patterns>
```

## Step 6: Write test-harness.json

Create `${DIRIGENT_RUN_DIR}/test-harness.json` with commands from the chosen stack files. This file is consumed by the test step and the planner.

```json
{
  "commands": {
    "build": {
      "command": "{build command from stack file, if applicable}",
      "explanation": "{what it builds}"
    },
    "test": {
      "command": "{test command from stack file}",
      "explanation": "{what it tests}"
    },
    "dev": {
      "command": "{run command from stack file}",
      "explanation": "{starts the dev server}"
    }
  },
  "env_vars": {},
  "portal": {
    "start_command": "{run command from stack file}",
    "port": {port from stack file},
    "url_after_start": "/"
  },
  "_sources": {
    "commands.test": "stacks/{stack-file}.md",
    "commands.dev": "stacks/{stack-file}.md",
    "portal.port": "stacks/{stack-file}.md"
  }
}
```

Only include command keys that apply. For example, a Streamlit app has no build step — omit `commands.build`. A Gradio app might not have a separate test command initially — omit `commands.test`.

For multi-stack combos, `commands.dev` should be the primary frontend/UI command. Document additional services in `notes`.

## Step 7: Write start.sh

Every greenfield project MUST produce a `start.sh` at the repo root. Use the "Start Script Pattern" from each stack file in the combo.

For multi-stack combos, the start script starts all services:

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

# Install dependencies
{install commands from each stack file}

# Start backend (if any)
{backend start command} &

# Start frontend
exec {frontend start command}
```

The start script must:
- Be self-contained (installs deps, starts everything)
- Bind to `0.0.0.0` (not localhost) for port-forwarding
- Print the URLs/ports on startup
- Use `exec` for the foreground process

## Step 8: Validate

Before committing:

1. **Every tool in the combo is installed** — verified in Step 2
2. **Every command comes from the stack files** — no invented commands
3. **start.sh actually runs** — execute it and verify the app starts
4. **Test commands work** — run the test command from the stack file
5. **test-harness.json is valid** — parseable JSON with the correct schema
6. **`<key-patterns>` includes opinionated defaults** — not just naming conventions
7. **Keep it proportional** — a small feature needs 1 page of architecture, not 10

## Step 9: Commit

```bash
git add ARCHITECTURE.md start.sh
git commit -m "docs: greenfield scaffold — {combo name}, testing strategy, start script"
```

Note: test-harness.json lives in `${DIRIGENT_RUN_DIR}`, not the repo — do not commit it.

## Rules

<rules>
<rule>Pick the stack from the archetype table — do not deliberate or propose alternatives</rule>
<rule>Read the stack files in stacks/ for exact commands — do not invent scaffold, run, or test commands</rule>
<rule>Copy the relevant opinionated defaults from stacks/README.md into <key-patterns> — this is how the executor learns them</rule>
<rule>Create test-harness.json in ${DIRIGENT_RUN_DIR} — the test step and planner depend on it</rule>
<rule>Every greenfield project MUST produce a start.sh that starts the full app</rule>
<rule>start.sh MUST bind to 0.0.0.0 for port-forwarding access</rule>
<rule>Match recommendations to project scale — a weekend project doesn't need the same architecture as a SaaS platform</rule>
<rule>Every recommendation must have a concrete reason tied to the spec</rule>
<rule>If the repo already has a framework config, skip scaffolding and work with what exists</rule>
<rule>Test strategy must be executable — commands from the stack files, not concepts</rule>
<rule>NEVER write framework config files manually — always use the official scaffolder</rule>
<rule>Do not over-engineer — if the spec describes 3 endpoints, don't propose a microservice architecture</rule>
<rule>Acknowledge what you don't know — put it in "Decisions NOT Made"</rule>
</rules>

<constraints>
<constraint>Output: ARCHITECTURE.md + start.sh (in repo) + test-harness.json (in ${DIRIGENT_RUN_DIR})</constraint>
<constraint>Maximum 15 minutes</constraint>
<constraint>Architecture sections should be under 200 lines — these get consumed by the planner, not published as docs</constraint>
</constraints>
