---
name: build-manifest
description: Analyze the current repo and generate outbid-test-manifest.yaml with test infrastructure, components, and preview config
arguments: --interactive (optional) - ask the user to confirm/adjust each section before writing
---

# Build Test & Preview Manifest

Analyze this repository and generate `outbid-test-manifest.yaml` at the repo root.

The manifest tells an AI agent landing in a sandbox: "Here's what exists in this repo, here's how developers actually work with it, here's how to verify your changes."

## Mode

Check if `$ARGUMENTS` contains `--interactive`.

- **Default (autonomous)**: Analyze, generate, validate, done. No questions.
- **Interactive (`--interactive`)**: After analyzing, walk the user through each manifest section before writing. See **Interactive Mode** at the end of this skill.

## Schema & Example

Read these files from the skill directory before generating:

- **`schema.py`** — Pydantic models. Your output YAML must conform to these types.
- **`example.yaml`** — Full example showing every field.

### Key schema rules

- `components`: dict keyed by name (preferred)
- `Component.start`: always use the nested object form (`start.command`, `start.ready_check.type/target/timeout`). NEVER put `timeout` as a sibling of `start`.
- `prerequisites`: use the `Prerequisites` object with `tools` and `env_vars` keys
- `gaps`: use `Gap` objects (not plain strings)

---

## Step 1: Find the developer workflow

The #1 goal is to discover how developers ACTUALLY work with this repo. Do NOT decompose infrastructure into atomic commands — find the orchestration layer.

### Priority order for discovery

**1. Task runners / orchestration (READ THESE FIRST)**
```
justfile, Makefile, Taskfile.yml, package.json (scripts section)
```
These define the real commands developers use. A `just up` that starts the whole stack is better than 5 individual `docker compose up -d <service>` commands.

**2. Docker/compose files (for understanding what's in the stack)**
```
docker-compose.yml, docker-compose.yaml, compose.yml, compose.yaml
```
Read these to understand WHAT services exist, but prefer the task runner commands to START them.

**3. Project config (for prerequisites and test commands)**
```
pyproject.toml, package.json, Makefile, tox.ini, setup.cfg
```

**4. Secrets management**
```
.doppler.yaml, doppler.yaml, .env.example, .env.sample
```

**5. CI config (to cross-check test commands)**
```
.github/workflows/*.yml, .gitlab-ci.yml
```

**6. Test infrastructure**
```
conftest.py, tests/conftest.py, tests/__init__.py
tests/, test/, __tests__/, spec/
```

**7. Documentation (verify against code, never trust blindly)**
```
README.md, CONTRIBUTING.md, docs/
```

### What to extract

For each discovery source, extract:

**From task runners (justfile/Makefile/package.json scripts):**
- The "start everything" command (e.g. `just up`, `make dev`, `npm run dev`)
- The "setup from scratch" command (e.g. `just setup`, `make install`)
- The "run tests" commands (e.g. `just test`, `make test`, `npm test`)
- The "seed/populate test data" command if any (e.g. `just sync-prod-to-local`, `make seed`, `python manage.py loaddata`)
- Any other developer-facing commands

**Look specifically for test data patterns:**
- Seed scripts or fixtures (`seeds/`, `fixtures/`, `tests/fixtures/`, `tests/data/`)
- Database dump imports (`*.sql`, `*.dump` files)
- Sync-from-production commands (anonymized snapshots, subset exports)
- Factory/faker-based generation (`factories.py`, `factory_boy`, `faker`)
- If tests rely on specific data state, how is that state created?

**From docker-compose:**
- What services are defined (postgres, redis, app, worker, etc.)
- Their ports and health checks
- Which are infrastructure (db, cache) vs application (app, worker, ui)

**From conftest.py / test fixtures:**
- What external services are auto-mocked in tests
- What fixtures exist (fake databases, stub APIs, etc.)

**From project config:**
- What tools are needed (python, node, uv, pnpm, docker, etc.)
- What linters/formatters are configured
- What test frameworks are used

### Critical rule: prefer orchestration over decomposition

If a justfile has `just up` that runs `docker compose up -d`, use `just up` as the start command. Do NOT decompose it into individual `docker compose up -d postgres`, `docker compose up -d redis` etc.

The agent should run the same commands a developer would. If a developer runs 2 commands to get a working environment, the manifest should have 2 commands — not 10.

### Workflow confidence check

After analyzing, classify what you found into one of three confidence levels:

**HIGH** — An orchestration layer exists (justfile, Makefile with dev targets, package.json with start/dev/test scripts). You can see the exact commands developers use.

**MEDIUM** — No task runner, but docker-compose + project config give a clear picture. You can reconstruct the workflow from compose files, CI config, and README. Mark reconstructed commands in the manifest with a YAML comment: `# inferred — no task runner found`.

**LOW** — Bare repo with no task runner, no docker-compose, no CI, sparse README. You can see individual tools (pytest exists, ruff is configured) but the "how do you start this?" story is unclear.

**What to do at each level:**

| Confidence | Autonomous mode | Interactive mode |
|------------|----------------|-----------------|
| HIGH | Generate normally | Confirm workflow with user |
| MEDIUM | Generate with `# inferred` comments on reconstructed commands | Run onboarding questionnaire (see below) |
| LOW | Generate L1 only (lint/test commands). Leave preview.start_command empty. Add a gap: "No developer workflow documented." | Run onboarding questionnaire (see below) |

**NEVER hallucinate a workflow.** If you don't find a start command, don't invent one. An empty `start_command` is better than a wrong one. An agent running a wrong command wastes more time than an agent that knows it doesn't have the answer.

### Onboarding questionnaire (interactive mode, MEDIUM/LOW confidence)

When confidence is MEDIUM or LOW and `--interactive` is set, run this questionnaire BEFORE generating any manifest content. These questions replace the normal interactive flow (Steps 1-6) — the answers feed directly into generation.

```
I couldn't find a clear developer workflow for this repo.
Let me ask a few questions so the manifest is accurate.

1. How do you start the full stack locally?
   (e.g. "just up", "docker compose up", "npm run dev", or describe the steps)

2. What setup does a new developer need from a fresh clone?
   (e.g. "just setup", or list the steps: install deps, setup secrets, migrate db, seed data)

3. How do you run tests?
   - Unit tests:
   - Integration tests (if any):
   - E2E tests (if any):

4. How do you get test data into your local environment?
   (e.g. "just seed", "make sync-prod", fixtures in tests/, dump import, nothing needed)
   If from production: is it anonymized? Is there a subset/sample command?

5. How are secrets managed?
   (e.g. Doppler, .env file, Vault, manual env vars)

6. Anything else an AI agent should know to work in this repo?
   (e.g. "always run X before committing", "Y is broken right now", "don't touch Z")
```

Ask all 6 questions at once (not one by one). Use the answers to fill in the manifest. If the developer says "I don't know" or "there isn't one" for a question, leave that section empty or document it as a gap.

After the questionnaire, proceed to the normal interactive confirmation flow (Steps 1-6) so the developer can verify the generated sections.

## Step 2: Check session history for working commands

Run this DuckDB query to find commands that actually worked in past sessions:

```bash
PROJECT_KEY=$(echo "$PWD" | sed 's|/|-|g')
SEARCH_PATH="$HOME/.claude/projects/-${PROJECT_KEY#-}/*.jsonl"

duckdb :memory: -c "
SELECT
  regexp_extract(message.content::VARCHAR, '\"command\":\"([^\"]+)\"', 1) AS command,
  CASE
    WHEN message.content::VARCHAR LIKE '%\"is_error\":true%' THEN 'FAILED'
    WHEN message.content::VARCHAR LIKE '%exit code 1%' THEN 'FAILED'
    WHEN message.content::VARCHAR LIKE '%exit code 0%' THEN 'OK'
    ELSE 'UNKNOWN'
  END AS result,
  timestamp
FROM read_ndjson('\$SEARCH_PATH', auto_detect=true, ignore_errors=true)
WHERE message.content::VARCHAR LIKE '%command%'
  AND (message.content::VARCHAR LIKE '%pytest%'
  OR message.content::VARCHAR LIKE '%npm%test%'
  OR message.content::VARCHAR LIKE '%ruff%'
  OR message.content::VARCHAR LIKE '%vitest%'
  OR message.content::VARCHAR LIKE '%just %'
  OR message.content::VARCHAR LIKE '%make %')
ORDER BY timestamp DESC
LIMIT 30;
"
```

Prefer commands that succeeded in recent sessions. If a command never appeared or always failed, document it as a gap instead.

## Step 3: Generate the manifest

Write `outbid-test-manifest.yaml` to the repo root. Follow this exact structure. Every section is REQUIRED (use empty values/lists if nothing applies).

```yaml
# outbid-test-manifest.yaml — [repo name]
# Generated by dirigent:build-manifest

test_level: <1 or 2>

prerequisites:
  tools:
    - name: <tool>
      check: "<command that proves it's installed>"
      install_hint: "<how to install it>"
      required_version: "<version constraint or empty>"
    # ... one entry per required tool
  env_vars:
    - name: <VAR_NAME>
      source: "<where it comes from>"
      secret: <true/false>
    # ... one entry per required env var

components:
  <service_name>:
    type: <database|cache|queue|external|backend|frontend|worker>
    runtime: <docker-compose|process>
    start:
      command: "<the ACTUAL command developers use to start this>"
      ready_check:
        type: <http|tcp|log|delay>
        target: "<check target>"
        timeout: <seconds>
    endpoint:
      host: <hostname>
      port: <port>
      protocol: <tcp|http>
    depends_on: [<other component names>]

  # For auto-mocked services (conftest fixtures etc.)
  <mocked_service>:
    type: external
    mock:
      strategy: stub
      config:
        note: "<where/how it's mocked>"

levels:
  l1:
    pre_commands:
      - "<install/setup commands needed before L1 tests>"
    commands:
      - name: <test-name>
        run: "<exact shell command>"
        expect: exit_0
      # ... all L1 commands (unit tests, lint, format, type-check)
  l2:
    pre_commands:
      - "<commands to start services needed for L2>"
    commands:
      - name: <test-name>
        run: "<exact shell command>"
        expect: exit_0
        needs: [<component names that must be running>]
      # ... all L2 commands (integration, e2e, api tests)

gaps:
  - area: "<what's missing>"
    reason: "<not_configured|requires_hardware|incomplete|not_applicable>"
    description: "<human-readable explanation>"
    mitigation: "<how to cope without it>"
    risk: <low|medium|high>

preview:
  start_command: "<THE command to start the dev server / full stack>"
  port: <main port the user sees>
  framework: "<detected framework(s)>"
  health_check: "<health endpoint path>"
  setup_steps:
    - "<step 1: install deps>"
    - "<step 2: setup secrets>"
    - "<step 3: start stack>"
    - "<step 4: seed data (if applicable)>"
  uses_doppler: <true/false>
  doppler_project: "<project name>"
  doppler_config: "<config name>"

# Agentic development readiness
readiness:
  score: <0-10>
  rationale: "<1-2 sentence explanation>"
```

### Section-by-section rules

**prerequisites.tools:**
- Only tools the developer must have installed locally
- `check` must be a command that exits 0 if the tool is present
- Include version constraints if the project requires a specific version

**prerequisites.env_vars:**
- Every env var that test commands or preview need
- Mark `secret: true` for credentials, API keys, tokens
- `source` should say WHERE to get it (Doppler config name, .env file, manual)

**components:**
- List what's in the stack (from docker-compose/compose files)
- For `start.command`: use the **task runner command** if one exists (`just up`, `make dev`), not raw docker-compose commands. Only fall back to `docker compose up -d <service>` if there's no orchestration layer.
- If one command starts the whole stack, put that command on ONE component (the main one) and leave `start` empty on the others. Or better: use `l2.pre_commands` to start everything at once.
- Mock components: only for things auto-mocked in test fixtures. Include the fixture name/location in `config.note`.

**levels.l1 (fast, no services):**
- Unit tests, lint, format checks, type checks
- These must run WITHOUT any external services or secrets
- If a test command needs secrets even for unit tests (e.g. `doppler run -- pytest`), that's fine — document it, the agent will check if Doppler is available
- `pre_commands`: install dependencies (e.g. `uv sync`, `pnpm install`)

**levels.l2 (needs services):**
- Integration tests, API tests, E2E tests
- `pre_commands`: start the stack (e.g. `just up`, `docker compose up -d`). Use the SAME command developers use. ONE command if possible.
- `needs`: which components from the `components` section must be running

**gaps:**
- Things that SHOULD exist but don't
- Be specific: "No type checking configured" not "Testing could be improved"
- `reason`: why it's missing
- `mitigation`: how the project copes without it

**preview:**
- `start_command`: THE command that gives you a running app you can interact with. This is what a developer runs after setup. Prefer task runner commands (`just up`, `make dev`, `npm run dev`).
- `port`: the main port the user/agent sees (frontend port if full-stack, API port if backend-only)
- `setup_steps`: ordered list of everything needed from a fresh clone to a running app. Think "new developer onboarding". Include secrets setup, dependency install, db migration, **and test data seeding**. If there's a seed/sync command, it belongs here.
- `framework`: what the agent is working with (e.g. "Next.js + FastAPI", "Django", "Express")

### Doppler detection

Check for Doppler usage:
- `.doppler.yaml` or `doppler.yaml` in root
- `doppler run` in justfile, Makefile, package.json scripts
- `doppler` mentioned in README.md or .env.example

If Doppler is detected: set `uses_doppler: true`, extract project/config from doppler config file.

### Readiness score

After generating all sections, compute a `readiness.score` (0-10) that tells agents and humans how well-equipped this repo is for autonomous AI development.

**Scoring rubric — add points for each:**

| Points | Criterion |
|--------|-----------|
| +2 | L1 tests exist and commands are verified (lint, unit tests) |
| +1 | L2 tests exist (integration/e2e) |
| +1 | Orchestration layer exists (justfile/Makefile/scripts — not raw docker commands) |
| +1 | Preview/dev server can be started with a single command |
| +1 | Test data seeding is automated (seed script, fixtures, sync command) |
| +1 | Secrets management is automated (Doppler, Vault — not manual .env copying) |
| +1 | CI/CD pipeline exists (.github/workflows, etc.) |
| +1 | External services are auto-mocked in tests (conftest fixtures) |
| +1 | Setup from fresh clone is <= 3 commands |

**Deduct points for:**

| Points | Criterion |
|--------|-----------|
| -1 | No tests at all |
| -1 | No preview/start command found (or inferred with low confidence) |
| -1 | Manual setup steps required (copy .env, manually create DB, etc.) |
| -1 | High-risk gaps (e.g. no CI, no type checking on a typed codebase) |

Floor at 0, cap at 10.

**Rationale:** Write 1-2 sentences explaining the score. Focus on what an agent CAN do and what will trip it up.

Examples:
- `score: 8` / `"Strong setup: just up starts everything, L1+L2 tests verified, Doppler handles secrets. Missing CI pipeline and type checking."`
- `score: 3` / `"Unit tests exist but no orchestration layer, no integration tests, manual .env setup required. Agent can lint and run unit tests but cannot start the app."`
- `score: 0` / `"No tests, no start command, no documentation. Agent is flying blind."`

### README caveat

READMEs are frequently outdated. If README and actual code contradict each other, trust the code. Verify every command/path against what actually exists.

## Step 4: Validate

After writing the manifest, verify it parses correctly:

```bash
python3 -c "
import sys, yaml
from pathlib import Path
raw = yaml.safe_load(Path('outbid-test-manifest.yaml').read_text())

errors = []

# Required top-level keys
for key in ['test_level', 'prerequisites', 'components', 'levels', 'gaps', 'preview']:
    if key not in raw:
        errors.append(f'Missing required key: {key}')

# Check levels
levels = raw.get('levels', {})
if 'l1' not in levels:
    errors.append('Missing levels.l1')
if raw.get('test_level', 1) >= 2 and 'l2' not in levels:
    errors.append('test_level=2 but no levels.l2')

# Check l1 has commands
l1 = levels.get('l1', {})
if not l1.get('commands'):
    errors.append('levels.l1 has no commands')

# Check preview
warnings = []
preview = raw.get('preview', {})
if not preview.get('start_command'):
    warnings.append('preview.start_command is empty (ok if workflow is unknown)')
if not preview.get('port'):
    warnings.append('preview.port is empty')
if not preview.get('framework'):
    warnings.append('preview.framework is empty')
if not preview.get('setup_steps'):
    warnings.append('preview.setup_steps is empty')

# Check component nesting (catch common YAML mistakes)
for comp_name, comp in raw.get('components', {}).items():
    if isinstance(comp, dict):
        if 'timeout' in comp and 'start' in comp:
            errors.append(f'components.{comp_name}.timeout should be inside start.ready_check, not at component level')

if errors:
    print('VALIDATION FAILED:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)

if warnings:
    print('WARNINGS:')
    for w in warnings:
        print(f'  - {w}')

print(f'test_level: {raw.get(\"test_level\")}')
print(f'levels: {list(levels.keys())}')
comps = raw.get('components', {})
if isinstance(comps, dict):
    real = [k for k, v in comps.items() if isinstance(v, dict) and 'mock' not in v]
    mocked = [k for k, v in comps.items() if isinstance(v, dict) and 'mock' in v]
else:
    real = [c.get('name') for c in comps if not c.get('mock')]
    mocked = [c.get('name') for c in comps if c.get('mock')]
print(f'components: {len(real)} real, {len(mocked)} mocked')
print(f'gaps: {len(raw.get(\"gaps\", []))}')
print(f'preview: {preview.get(\"framework\")} on :{preview.get(\"port\")}')
print('Manifest OK')
"
```

## Output

After generating, summarize and end with the readiness score:

- Test levels available (L1, L2)
- Number of test commands per level
- Components (real vs mocked)
- Gaps found
- Preview: framework, port, start command
- Setup flow (the ordered steps from zero to running)
- **Agentic Development Readiness: X/10** — rationale

---

## Interactive Mode

When `--interactive` is passed, run Steps 1-2 (analysis + session history) silently, then check workflow confidence.

**If confidence is HIGH:** proceed to the normal confirmation flow below, starting with "1. Developer workflow".

**If confidence is MEDIUM or LOW:** run the onboarding questionnaire FIRST (defined in Step 1 above), then use the answers to pre-fill the confirmation flow below. The developer's answers override anything you inferred.

### 1. Developer workflow

Present the workflow you discovered (or reconstructed from questionnaire answers) FIRST — this is the most important thing to get right:

```
Here's how I think developers work with this repo:

Setup (from fresh clone):
  1. just setup         → install deps, setup tooling
  2. doppler login      → configure secrets
  3. just up            → start the full stack
  4. just seed          → populate dev database

Start (day-to-day):
  just up               → starts everything (postgres, redis, app, worker, ui)

Test:
  just test             → runs all tests
  pytest tests/unit     → unit tests only

Is this right? What's missing or wrong?
```

For MEDIUM/LOW confidence, be transparent about what you inferred vs what you observed:

```
I couldn't find a task runner (no justfile, Makefile, or npm scripts).
Here's what I pieced together from docker-compose and project config:

Setup (from fresh clone):
  1. pip install -e ".[dev]"             # inferred from pyproject.toml
  2. docker compose up -d                # inferred from compose.yaml
  3. alembic upgrade head                # inferred from alembic.ini

I'm not confident about this. Is this how you actually work with this repo?
```

### 2. Prerequisites

```
Tools needed:
  - python (python3 --version) >=3.11
  - node (node --version) >=18
  - docker (docker --version)
  - just (just --version)
  - doppler (doppler --version)

Env vars needed:
  - DATABASE_URL (Doppler dev_personal, secret)
  - REDIS_URL (Doppler dev_personal, secret)

Add, remove, or change anything? (enter to confirm)
```

### 3. Components & mocks

```
Stack components:
  - postgres (database, port 5432)
  - redis (cache, port 6379)
  - app (backend, port 8213)
  - worker (worker, port 8215)
  - ui (frontend, port 3213)

Started by: just up (single command)

Auto-mocked in tests:
  - openai_api (stub via conftest.py)
  - fakeredis (fakeredis library)

Add, remove, or change anything? (enter to confirm)
```

### 4. Test levels

```
L1 (no services needed):
  - unit-tests: pytest tests/unit -x -q
  - lint: ruff check src/
  - format-check: ruff format --check src/

L2 (needs stack running):
  pre: just up && sleep 10
  - integration: doppler run -- pytest tests/integration -x -q (needs: postgres, redis)
  - e2e: cd ui && npx playwright test (needs: app, ui)

test_level: 2

Add, remove, or change anything? (enter to confirm)
```

### 5. Gaps

```
Known gaps:
  - Type checking (not_configured, risk: medium)
  - CI/CD pipeline (not_configured, risk: high)
  - Load testing (requires_hardware, risk: low)

Any other gaps to add? Anything to remove? (enter to confirm)
```

### 6. Preview

```
Preview config:
  framework:      Next.js + FastAPI
  start_command:  just up
  port:           3213
  health_check:   /api/health

  Setup from scratch:
    1. just setup
    2. doppler login && doppler setup
    3. just up
    4. just sync-prod-to-local

  uses_doppler:     true
  doppler_project:  customer_cube
  doppler_config:   dev_personal

Change anything? (enter to confirm)
```

### 7. Write

After all sections are confirmed, write the manifest and run validation (Step 4).

If the user changed something, incorporate their changes. If they added something you're unsure about, flag it but include it — the user knows their repo better than you do.
