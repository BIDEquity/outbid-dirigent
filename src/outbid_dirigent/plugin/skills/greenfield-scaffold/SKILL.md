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

## File Routing — Where Everything Lives

Use this table to navigate the skill. **Read only what you need for the current step** — don't pre-load everything.

| You need... | Go to | When |
|---|---|---|
| **Stack catalog + opinionated defaults** | `stacks/README.md` | Step 1A — pick the stack combo |
| **Architecture catalog + matrices** (Interaction Shape / Compute Topology / Domain Pattern) | `stacks/architecture-patterns/README.md` | Step 1B — pick one from each axis |
| **Stack-specific commands** (scaffold, run, test, install-check) | `stacks/<stack-name>.md` (e.g. `stacks/streamlit.md`) | Step 2 (availability check), Step 4 (scaffold), Step 6 (test-harness), Step 7 (start.sh) |
| **Pattern-specific code skeleton** | `stacks/architecture-patterns/<pattern>.md` (e.g. `stacks/architecture-patterns/streaming.md`) | Step 5 — write `### Pattern Implementation Skeleton` into ARCHITECTURE.md |
| **Migration thresholds per stack** | `stacks/evolution-thresholds.md` | Step 5 — write `### Evolution Thresholds` into ARCHITECTURE.md |
| **Framework API / latest syntax** | context7 MCP (`mcp__context7__resolve-library-id` + `query-docs`) | Anywhere you're tempted to recall API from memory — query instead |

## Steps At A Glance

| # | Step | Output |
|---|---|---|
| 1 | Classify SPEC: Stack + Pattern + Out-of-Scope hints | Decisions in memory |
| 2 | Verify stack availability | Pass/fail |
| 3 | Assess existing repo structure | Skip-scaffold flag |
| 4 | Run scaffold commands | Project skeleton on disk |
| 4.5 | **Install E2E framework (mandatory for web archetypes)** | `@playwright/test` in devDependencies + `playwright.config.ts` + first smoke spec |
| 5 | Write ARCHITECTURE.md | `<testing-verification>`, `<architecture-decisions>`, `<key-patterns>` |
| 6 | Write test-harness.json | `${DIRIGENT_RUN_DIR}/test-harness.json` (MUST include `e2e_framework` for web archetypes) |
| 7 | Write start.sh | `start.sh` at repo root, executable, binds 0.0.0.0 |
| 8 | Validate | All outputs verified |
| 9 | Commit | `ARCHITECTURE.md` + `start.sh` + `playwright.config.ts` + smoke spec committed |

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

This is strongly recommended — your training data may be stale. Scaffold commands, config formats, and API surfaces change between versions.

**Missing context7 is not a reason to skip install steps.** Stable install/scaffold commands (e.g. `npm install -D @playwright/test`, `npx create-next-app`) do not require a docs lookup. Skipping them because context7 is unavailable caused the failure this skill is being hardened against. Use context7 for API/syntax recall _while writing code_; do not use its absence to opt out of mandatory install steps.

## Step 1: Classify the SPEC (TWO dimensions)

Read `${DIRIGENT_RUN_DIR}/SPEC.md` and classify in TWO orthogonal dimensions:

### 1A: Use-Case-Archetype → Stack

Match the SPEC to an archetype from `stacks/README.md` and pick the stack combo. Read the "Typical Pattern" column too — it tells you the default for 1B.

| SPEC Shape | Combo | Typical Pattern | Stack Files to Read |
|---|---|---|---|
| "Dashboard for CSV data" | Streamlit + DuckDB | Sync REST | `stacks/streamlit.md`, `stacks/duckdb.md` |
| "Live dashboard for sensor data" | Streamlit + DuckDB | Streaming | `stacks/streamlit.md`, `stacks/duckdb.md` |
| "API + frontend app" | FastAPI + Vite+React | Sync REST | `stacks/fastapi.md`, `stacks/vite-react.md` |
| "Event-driven workflow API" | FastAPI + Supabase Local | Event-Driven | `stacks/fastapi.md`, `stacks/supabase-local.md` |
| "ETL pipeline" | FastAPI + DuckDB | Pipeline / ETL | `stacks/fastapi.md`, `stacks/duckdb.md` |
| "Scheduled report generator" | FastAPI + SQLite | Batch | `stacks/fastapi.md`, `stacks/sqlite.md` |
| "Full-stack app with auth" (simple) | Next.js + PocketBase | Sync REST | `stacks/nextjs.md`, `stacks/pocketbase.md` |
| "Full-stack app with auth" (production) | Next.js + Supabase Local | Sync REST | `stacks/nextjs.md`, `stacks/supabase-local.md` |
| "Collaborative whiteboard" | Next.js + Supabase Local | Real-time | `stacks/nextjs.md`, `stacks/supabase-local.md` |
| "App with database" | FastAPI + SQLite | Sync REST | `stacks/fastapi.md`, `stacks/sqlite.md` |
| "Chatbot / AI assistant" | Streamlit + Anthropic SDK | Streaming | `stacks/streamlit.md`, `stacks/anthropic-sdk.md` |
| "Document Q&A / search" | Streamlit + LanceDB + Anthropic SDK | Streaming | `stacks/streamlit.md`, `stacks/lancedb.md`, `stacks/anthropic-sdk.md` |
| "AI agent with tools" | FastAPI + Anthropic SDK | Agent Loop | `stacks/fastapi.md`, `stacks/anthropic-sdk.md` |
| "AI-powered data analysis" | Streamlit + DuckDB + Anthropic SDK | Agent Loop | `stacks/streamlit.md`, `stacks/duckdb.md`, `stacks/anthropic-sdk.md` |
| "ML model demo" | Gradio | Sync REST | `stacks/gradio.md` |
| "Mobile app" (simple) | Expo + PocketBase | Sync REST | `stacks/expo.md`, `stacks/pocketbase.md` |
| "Mobile app" (production) | Expo + Supabase Local | Sync REST | `stacks/expo.md`, `stacks/supabase-local.md` |
| "Mobile app with scanning/camera/NFC" | Expo + Supabase Local | Event-Driven | `stacks/expo.md`, `stacks/supabase-local.md` |
| "Internal tool / form app" | Streamlit | Sync REST | `stacks/streamlit.md` |
| "Docs site / landing page" | Astro Starlight | — (static) | `stacks/astro-starlight.md` |
| Default (unclear) | Streamlit | Sync REST | `stacks/streamlit.md` |

### 1B: Architecture — Three Axes

Read `stacks/architecture-patterns/README.md`. Architecture is not one dimension — pick **three** things:

**1B-i: Interaction Shape (1 of 5)** — how clients interact with the system:
- **Sync REST / CRUD** (default, 80% of prototypes)
- **Streaming** — "live", "as it happens", LLM streaming
- **Event-Driven** — "when X happens then Y", webhooks, triggers
- **Real-time / Collaborative** — shared state across clients
- **Batch / Scheduled** — cron, nightly, hourly

Start with the "Typical Pattern" from 1A. Override only if the SPEC's domain problem demands a different shape.

**1B-ii: Compute Topology (1 of 3)** — where the code runs:
- **In-Process** (default) — single long-lived process (FastAPI, Streamlit, Next.js dev)
- **Serverless / Edge** — short-lived functions (Supabase Edge, Vercel Functions). Pick when the stack is natively serverless.
- **Long-running Worker** — dedicated background process. Pick when work is async / takes minutes / needs retries.

**1B-iii: Domain Pattern (0 or 1 — optional)** — shape of the problem:
- **Pipeline / ETL** — sequential stages with clear I/O
- **Agent Loop** — LLM with tool use, self-directed
- **State Machine / Workflow** — entity with sequential states + error paths (use this, NOT Event-Driven, when ordering and error recovery matter)
- **Webhook Receiver** — external trigger (usually Serverless)
- **Multi-Tenant Isolation** — orthogonal; applies regardless of other axes

Most prototypes need zero Domain Patterns. Only add one when the SPEC's problem shape matches.

### 1C: Verify Stack × Interaction Shape Compatibility

Check the Stack × Interaction Shape Matrix in `stacks/architecture-patterns/README.md`. Your chosen stack must be ✓ (or at worst △) for your chosen shape. If it's ✗, reconsider one of the two choices.

Also check the Compute Topology × Stack table — make sure your stack naturally supports your chosen topology.

### 1D: Read Out-of-Scope / Future Hints

Read the "Out of Scope", "Later", "Future", or "Not in this phase" sections of the SPEC. These items are NOT being built now but they heavily influence current architectural decisions:

- **If SPEC says "later: live updates"** → current Sync REST choice should keep `data.py` return shapes compatible with async generators (don't cache eagerly)
- **If SPEC says "eventually: multi-user collaboration"** → avoid Streamlit (session-only) for parts that might need Real-time later; prefer FastAPI + client-agnostic state
- **If SPEC says "future: move to Postgres"** → keep SQL standard in `data.py`, avoid SQLite-specific features (UPSERT quirks, JSON1 extensions)
- **If SPEC says "later: mobile app"** → web choice should expose a proper API layer, not a Streamlit-only blob

Capture these in the `### Future Considerations` block of `<architecture-decisions>` so downstream tasks respect them.

**Do NOT deliberate beyond 2 minutes.** Match SPEC signals → stack + pattern → verify compatibility → note future hints → move on.

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

### Step 4a — Replace the stock landing page (MANDATORY for web archetypes)

`create-next-app` / `npm create vite` ship a Vercel tutorial / Vite logo page. **Leaving it in place is the failure mode this step prevents.** A user who opens the finished app sees "To get started, edit app/page.tsx" with a Next.js logo — no navigation, no branding, no path forward — even after every downstream phase "succeeded."

Immediately after running the scaffold, overwrite the stock landing with a minimal, app-branded home that:

1. Uses a heading derived from the SPEC's working title (not "Create Next App").
2. Links to the first real route the app will have (typically `/login` for auth-bearing archetypes, or the first nav target for auth-less apps).
3. Does **not** reference the framework tutorial, Vercel templates, or starter docs.

Concrete per-stack templates:

- Next.js App Router → `stacks/nextjs.md` → "Stock Landing Replacement" section
- Vite + React → `stacks/vite-react.md` → "Stock Landing Replacement" section

The landing stays deliberately minimal — it's a placeholder that proves navigation works end-to-end, not a marketing page. The first real user-facing phase will flesh it out.

**Why this is a scaffold-phase concern, not a task-01 concern:** every downstream phase assumes the app has a reachable home. A nav component that `Link`s to `/` should land on *something*, not on a Vercel tutorial. Leaving it until later means every e2e smoke spec passes against garbage, and the "app works" signal becomes a lie.

## Step 4.5: Install E2E framework (MANDATORY for web archetypes)

If the chosen archetype has a browser-observable surface (any combo in the "Web Apps" table of `stacks/README.md`, plus all archetypes that include Next.js, Vite+React, Streamlit, or Gradio), install Playwright **unconditionally**.

**This step is non-skippable.** "context7 not available" is NOT a valid reason to skip — the install command is stable and does not require docs lookup:

```bash
npm install -D @playwright/test
npx playwright install --with-deps chromium
# If --with-deps fails (no sudo), fall back to:
npx playwright install chromium
```

Then commit a minimal `playwright.config.ts` and a first smoke spec at `tests/e2e/smoke.spec.ts`. The exact config/spec templates live in the stack file (`stacks/nextjs.md` → "E2E (Playwright)" section, `stacks/vite-react.md` → "E2E (Playwright)" section). Copy them verbatim and adjust only the `baseURL` / `webServer.command` to match the chosen port.

### 4.5a — Seed deterministic test credentials

Playwright specs cannot log in if nobody exists. Every web archetype with auth MUST seed at least one test user at scaffold time. Default credentials (use these exact values — downstream tests reference them):

```
admin@test.local / testpass123
```

Implementation per backend stack:

| Backend | Seed mechanism |
|---|---|
| PocketBase | Migration file in `pb_migrations/*_seed_test_user.js` using `app.save(new Record(...))` on the `users` collection. |
| Supabase Local | SQL in `supabase/seed.sql` — `INSERT INTO auth.users (...)`. Runs on `supabase db reset`. |
| FastAPI + SQLModel | Function `seed_test_users()` called from the `startup` lifespan hook when `ENV != "production"`. |
| Next.js API routes + SQLite | Module `src/lib/seed.ts` called from `start.sh` before the dev server starts. |

The seed MUST be idempotent — running the scaffold twice must not fail or duplicate users.

### 4.5b — Document the test credentials

The credentials from Step 4.5a MUST be visible to a new developer without grep:

1. **README.md `## Local Development` section** — a three-line block showing the credentials and where they come from.
2. **Dev-mode banner on the home page (strongly recommended)** — a small, dismissable component that reads `process.env.NODE_ENV === 'development'` (Next.js) or `import.meta.env.DEV` (Vite) and renders the test credentials inline. Never rendered in production builds. Templates in `stacks/nextjs.md` ("Dev Credentials Banner") and `stacks/vite-react.md` ("Dev Credentials Banner").

Why both? README is greppable but easy to miss. The on-page banner makes the failure "I don't know the test password" impossible — the next developer to open the app sees it in the first second.

**Rule:** if you do not finish Step 4.5, you do not proceed to Step 5. The contract negotiator downstream uses the presence of `e2e_framework` in `test-harness.json` (Step 6) to decide whether to write user-journey criteria backed by real browser tests or to fall back to weaker curl-based probes. Skipping this step silently degrades every downstream phase.

**Mobile archetypes (Expo):** Playwright is not the right tool — defer to `stacks/expo.md` for the Expo-specific e2e approach (Detox / Maestro). The seed-data + documentation rules still apply (seed a test account in the backend, document credentials in README).

**Non-web archetypes (pure ETL, batch jobs):** No e2e framework needed — record `"e2e_framework": null` in `test-harness.json` and move on. Seed data and credential documentation are not required when there is no login surface.

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
Archetype: {archetype from Step 1A}
Combo: {list of stacks}
Rationale: {1-2 sentences why this combo fits the SPEC}

### Architecture (three axes)

**Interaction Shape:** {Sync REST / Streaming / Event-Driven / Real-time / Batch}
Rationale: {1 sentence why this shape matches the domain problem}

**Compute Topology:** {In-Process / Serverless / Long-running Worker}
Rationale: {why this topology fits the SPEC + chosen stack}

**Domain Pattern:** {None / Pipeline / Agent Loop / State Machine / Webhook Receiver / Multi-Tenant}
Rationale: {only if applicable; most prototypes have none}

Stack Compatibility: ✓ (verified against matrix in architecture-patterns/README.md)

### Pattern Implementation Skeleton
{3-5 line code skeleton showing the Interaction Shape for this stack combo.
 Copy from the matching architecture-patterns/<shape>.md "Code Example" section.
 If a Domain Pattern is also used, show how it nests inside.}

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

### Future Considerations (Out-of-Scope Hints)
{Read SPEC's "Out of Scope" / "Future" / "Later" sections. List items that
 are NOT being built now but will influence future evolution:

 - {Future feature}: {which pattern/stack change it implies}

 Example:
 - "Live updates for sensor data" (out of scope): would shift pattern
   from Sync REST to Streaming — keep data.py functions return-shape
   compatible with async generators.
 - "Multi-user collaboration" (later): would require Real-time pattern —
   avoid session-only state patterns in data.py.
 - "Move to Postgres" (future): keep data.py SQL standard, no
   SQLite-specific features.}

Empty if the SPEC has no out-of-scope or future hints.

### Evolution Thresholds
{MANDATORY. Read `stacks/evolution-thresholds.md` and copy relevant rows for
 the chosen stack combo. Use concrete numbers, not adjectives.

 | Component | Threshold | Next step |
 |---|---|---|
 | {Stack 1} | {quantitative limit} | {concrete next stack} |
 | {Stack 2} | {quantitative limit} | {concrete next stack} |

 ### Upfront Commitments (cannot be added late)
 {Only if applicable. Hardware / developer-program / cert registrations with
  lead time that MUST be started during prototype phase, not deferred.
  Examples: Apple Pass Type ID, APNs cert, Google Wallet issuer account.
  Empty if the prototype has no such dependencies.}
}

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
  "e2e_framework": {
    "name": "playwright",
    "run_command": "npx playwright test"
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
    "e2e_framework": "stacks/{stack-file}.md (E2E section)",
    "portal.port": "stacks/{stack-file}.md"
  }
}
```

**`e2e_framework` is MANDATORY for every web archetype.** Set to `null` only for non-web archetypes (pure ETL / batch / CLI). The contract negotiator reads this key to decide whether user-journey criteria run through the browser or fall back to weaker curl probes.

Only include command keys that apply. For example, a Streamlit app has no build step — omit `commands.build`. A Gradio app might not have a separate test command initially — omit `commands.test`.

For multi-stack combos, `commands.dev` should be the primary frontend/UI command. Document additional services in `notes`.

## Step 7: Write start.sh

Every greenfield project MUST produce a `start.sh` at the repo root. Use the "Start Script Pattern" from each stack file in the combo.

For multi-stack combos, the start script starts all services and honours a `PORT` env var for the frontend (plus stack-specific env vars for backends, e.g. `POCKETBASE_PORT`):

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

PORT="${PORT:-{frontend default}}"
BACKEND_PORT="${BACKEND_PORT:-{backend default}}"

# Install dependencies
{install commands from each stack file}

# Start backend (if any) — seed migration runs on first boot, idempotent
{backend start command honouring BACKEND_PORT} &

# Wait for backend health before printing credentials (prevents "try to log in, backend still booting")
for i in $(seq 1 15); do
  curl -sf "http://localhost:${BACKEND_PORT}/api/health" > /dev/null 2>&1 && break
  sleep 1
done

cat <<BANNER
──────────────────────────────────────────
  App URL        : http://localhost:${PORT}
  Backend        : http://localhost:${BACKEND_PORT}
  Test login     : admin@test.local / testpass123
                   (seeded on first run; dev-mode banner on every page)
  Override ports : PORT=4000 BACKEND_PORT=9000 ./start.sh
──────────────────────────────────────────
BANNER

exec {frontend start command honouring PORT}
```

The start script must:
- Be self-contained (installs deps, starts everything)
- Bind to `0.0.0.0` (not localhost) for port-forwarding
- **Honour a `PORT` env var** (frontend) and a matching env var for each backend (`POCKETBASE_PORT`, `SUPABASE_PORT`, etc.) — default to the stack file's documented port
- Print the URLs/ports **AND the seeded test credentials** on startup (the banner is the operator's ground truth — a dev who reads start.sh output MUST know how to log in)
- Use `exec` for the foreground process
- **Do NOT print production secrets** — the credentials in the banner are the seeded test-only ones; if the stack also has production-only secrets, they never touch start.sh

## Step 8: Validate

Before committing:

1. **Every tool in the combo is installed** — verified in Step 2
2. **Every command comes from the stack files** — no invented commands
3. **start.sh actually runs** — execute it and verify the app starts
4. **Test commands work** — run the test command from the stack file
5. **test-harness.json is valid** — parseable JSON with the correct schema
6. **`<key-patterns>` includes opinionated defaults** — not just naming conventions
7. **Keep it proportional** — a small feature needs 1 page of architecture, not 10
8. **E2E framework installed for web archetypes (Step 4.5)** — run these checks:
   ```bash
   # package.json contains @playwright/test
   grep -q '"@playwright/test"' package.json || echo "MISSING — re-run Step 4.5"
   # config file exists
   ls playwright.config.ts playwright.config.js 2>/dev/null || echo "MISSING playwright.config"
   # smoke spec exists
   ls tests/e2e/*.spec.ts tests/e2e/*.spec.js 2>/dev/null || echo "MISSING smoke spec"
   # test-harness.json has e2e_framework
   python3 -c "import json; d=json.load(open('${DIRIGENT_RUN_DIR}/test-harness.json')); assert d.get('e2e_framework'), 'e2e_framework missing'" || echo "MISSING e2e_framework in harness"
   ```
   Any MISSING message means Step 4.5 was skipped — go back and complete it before proceeding.
9. **Test credentials seeded and documented (Steps 4.5a + 4.5b)** — run these checks when the archetype includes auth:
   ```bash
   # README documents the test credentials
   grep -qE 'admin@test\.local|testpass123' README.md || echo "MISSING test credentials in README"
   # Seed migration / seed script exists somewhere in the repo
   (grep -rlE 'admin@test\.local|testpass123' pb_migrations supabase src 2>/dev/null | head -1) || echo "MISSING seed for test user"
   ```
   Any MISSING message means the developer opening the app will not know how to log in — go back and complete Steps 4.5a/4.5b.
10. **Stock landing replaced (Step 4a)** — run these checks for web archetypes:
    ```bash
    # Next.js: stock scaffold content gone
    ! grep -qE 'Get started by editing|app/page\.tsx|Vercel logomark|Deploy Now' src/app/page.tsx 2>/dev/null || echo "MISSING — Next.js stock landing not replaced"
    # Vite: stock scaffold content gone
    ! grep -qE 'Vite \+ React|count is \{|Edit <code>src/App\.tsx' src/App.tsx 2>/dev/null || echo "MISSING — Vite stock landing not replaced"
    ```
    Any MISSING message means a user opening the app will see a framework tutorial instead of the application — go back and complete Step 4a.
11. **start.sh honours PORT and prints credentials (Step 7)** — run these checks:
    ```bash
    # PORT env var is read with a default
    grep -qE 'PORT="?\$\{PORT:-' start.sh || echo "MISSING — start.sh does not honour PORT env var"
    # Test login is echoed on startup
    grep -qE 'admin@test\.local' start.sh || echo "MISSING — start.sh does not print test credentials"
    ```
    Any MISSING message means the start script fights a port conflict or hides the login — fix Step 7 before committing.

## Step 9: Commit

```bash
git add ARCHITECTURE.md start.sh
git commit -m "docs: greenfield scaffold — {combo name}, testing strategy, start script"
```

Note: test-harness.json lives in `${DIRIGENT_RUN_DIR}`, not the repo — do not commit it.

## Rules

<rules>
<rule>Pick the stack from the archetype table — do not deliberate or propose alternatives</rule>
<rule>Pick ONE Interaction Shape + ONE Compute Topology from stacks/architecture-patterns/README.md. Domain Pattern is optional (most prototypes have none). Verify stack compatibility via the matrix. Don't invent custom shapes.</rule>
<rule>State Machine beats Event-Driven for sequential workflows with error paths. If the SPEC describes "X then Y then Z with fallbacks", use State Machine in domain.py, not raw event fan-out.</rule>
<rule>Read SPEC's Out-of-Scope / Future sections and capture hints in <architecture-decisions> Future Considerations — they influence current decisions even if not implemented now</rule>
<rule>Write ### Evolution Thresholds into <architecture-decisions> with concrete numbers (not adjectives). Pull defaults from stacks/evolution-thresholds.md. If there are upfront commitments with lead time (Apple Pass Type ID, APNs cert, etc.) list them separately — they cannot be deferred.</rule>
<rule>Read the stack files in stacks/ for exact commands — do not invent scaffold, run, or test commands</rule>
<rule>Copy the relevant opinionated defaults from stacks/README.md into <key-patterns> — this is how the executor learns them</rule>
<rule>Create test-harness.json in ${DIRIGENT_RUN_DIR} — the test step and planner depend on it</rule>
<rule>Every greenfield project MUST produce a start.sh that starts the full app</rule>
<rule>start.sh MUST bind to 0.0.0.0 for port-forwarding access</rule>
<rule>start.sh MUST honour a `PORT` env var for the frontend (and a matching env var per backend, e.g. `POCKETBASE_PORT`). Defaults come from the stack file. This is the lightweight port-conflict escape hatch — a dev on a machine with port 3000 taken should not have to edit start.sh.</rule>
<rule>start.sh MUST print the seeded test credentials (admin@test.local / testpass123) in its startup banner. A dev reading the terminal output must know how to log in without grepping files.</rule>
<rule>For any web archetype, Step 4a MUST replace the stock create-next-app / Vite landing with a minimal app-branded home that links to the first real route. Leaving the Vercel tutorial / Vite logo in place means a user opening the finished app sees a framework starter instead of the application.</rule>
<rule>For any web archetype (browser-observable UI), Playwright install is mandatory in Step 4.5. The install commands are stable and do NOT require context7. Missing context7 / MCP is NOT a valid reason to skip this step. Downstream contract negotiators rely on the resulting `e2e_framework` entry in test-harness.json.</rule>
<rule>For any web archetype with auth, seed at least one deterministic test user (`admin@test.local` / `testpass123`) at scaffold time (Step 4.5a). The seed MUST be idempotent. Downstream Playwright specs cannot log in without it.</rule>
<rule>Document the seeded test credentials in README.md `## Local Development` AND in a dev-mode banner on the home page (Step 4.5b). Production builds MUST NOT render the banner.</rule>
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
