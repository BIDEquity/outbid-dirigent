---
name: increase-testability
description: Analyze testability gaps and produce concrete, priority-ranked ways to raise the testability score before any feature work begins.
context: fork
agent: infra-architect
---

# Increase Testability

You analyze a repo's **testability** — the ability to write tests that actually prove something — and produce a priority-ranked list of gaps with concrete fixes. Output is `${DIRIGENT_RUN_DIR}/testability-recommendations.json`, which the planner turns into tasks.

This runs on repos with weak test setups *before* new features ship. Get the gaps right and every downstream task lands on stable ground. Get them wrong and the team ships features onto untestable code.

## Testability ≠ Coverage

These are two different things. Be precise:

| | Testability | Coverage |
|---|---|---|
| **Measures** | Can you write a test that proves X? | How many lines/branches a test suite executes |
| **Fixed by** | Seed data, auth setup, health checks, injectable dependencies, real infra | Writing more assertions |
| **High-coverage, low-testability smell** | Tests mock everything, never hit a real DB, green on broken code | 90% coverage, production breaks on first real request |
| **Our goal** | Make it *possible* to write meaningful tests | Not in scope of this skill |

If the repo's problem is "we can't even start the app locally" or "there's no test DB" or "every test mocks the thing being tested" — that's a testability problem, and that's what this skill fixes.

## File Routing — Where Everything Lives

| You need... | Go to | When |
|---|---|---|
| **Current harness + score + gaps** (the input) | `${DIRIGENT_RUN_DIR}/test-harness.json` | Step 1 — read before anything else |
| **Scoring rubric** (0-10 bands) | Inlined below under `<scoring-rubric>` | Step 3 — to justify `current_score` and compute `potential_score` |
| **Category signals & fix patterns** | Inlined below under `<analysis-categories>` | Step 2 — when expanding the harness's gap list |
| **Framework config syntax** (pytest, vitest, playwright, etc.) | context7 MCP (`mcp__context7__resolve-library-id` + `query-docs`) | Step 3 — before writing stack-specific `concrete_steps` |
| **Spec & route reason** (why this skill was invoked) | `${DIRIGENT_RUN_DIR}/SPEC.md` | Step 1 — understand what the team plans to build next |

Single-file skill. Nothing else to load.

## Steps At A Glance

| # | Step | Output |
|---|---|---|
| 1 | Read `test-harness.json` + SPEC.md | current_score, rationale, gaps in memory |
| 2 | Expand repo-level signals per category | Full gap list |
| 3 | Score each recommendation (effort, impact) using the rubric | Ranked recommendations |
| 4 | Write `testability-recommendations.json` | File on disk |
| 5 | Sanity-check `potential_score ≤ 10` and impact math | Validated output |

## When This Runs

Testability route, after init (`run-init` produced the harness). You have:
- `${DIRIGENT_RUN_DIR}/test-harness.json` — authoritative `testability_score`, `testability_rationale`, `testability_description`, `testability_gaps`
- `${DIRIGENT_RUN_DIR}/SPEC.md` — what the team wants to build *after* testability improves
- The live repo — read whatever you need

You do NOT re-score from scratch. Trust the harness's `testability_score` as `current_score`. Your job is to turn the harness's `testability_gaps` (and whatever else you find) into concrete, rankable work.

## Step 1: Read the Inputs

```bash
cat ${DIRIGENT_RUN_DIR}/test-harness.json
cat ${DIRIGENT_RUN_DIR}/SPEC.md
```

Extract into memory:
- `testability_score` → this becomes `current_score` in output
- `testability_gaps[]` → each is a candidate recommendation
- `testability_description` → the baseline state
- `testability_rationale` → what already exists (don't re-propose it)
- `services[]` → what needs to be up for tests to pass
- `commands.test`, `commands.dev`, `e2e_test_command` → existing infra to extend, not replace

From SPEC: note what's being built next. A recommendation that unblocks the SPEC's main feature area outranks a generic improvement.

## Step 2: Expand Repo Signals Per Category

The harness's `testability_gaps` is a *starting list*, not exhaustive. For each category below, check the repo directly. If a gap exists and is not already in `testability_gaps`, add it to your working list.

Dev-server detection is owned by `run-init`; dev-server gaps surface via the harness's `testability_gaps` field and are not re-checked here.

<analysis-categories>
<category name="seed-data" priority="high">
**Signal:** No `seed/`, `fixtures/`, `factories/`, `prisma/seed.*`, `db/seeds/`, `conftest.py` without factory imports, empty test DB after migrations.
**Why it matters:** Tests on empty DBs pass trivially. Testability scores 5 without this, 7+ with realistic edge-case data.
**Fix pattern:** Seed script with (a) 2-3 user roles (admin, regular, viewer), (b) 5-10 sample records for each main entity, (c) edge-case rows (empty strings, nulls, max-length values, unicode, boundary dates).
</category>

<category name="test-infrastructure" priority="high">
**Signal:** No `pytest.ini`/`pyproject[tool.pytest]`, no `vitest.config`/`jest.config`, no `rspec` config. OR: framework exists but no fixtures / no test DB setup / no transactional rollback.
**Why it matters:** Without infra, every test reinvents setup. Tests drift, flake, and stop running.
**Fix pattern (Python):** pytest + fixtures in `conftest.py` + `pytest-postgresql` or `testcontainers` for real DB. `@pytest.fixture(scope="session")` for the DB, `scope="function"` with transactional rollback for isolation.
**Fix pattern (JS/TS):** vitest + a test-db setup in `vitest.setup.ts` + per-suite truncate OR a testcontainer. Avoid Jest globals — prefer explicit imports.
**Fix pattern (Ruby):** rspec + `DatabaseCleaner` with `:truncation` for feature specs, `:transaction` for units.
</category>

<category name="mock-replacement" priority="high">
**Signal:** Tests import `jest.mock` / `unittest.mock.patch` on the module being tested (not its boundary), OR mocks return hand-written fake data that doesn't match the real schema.
**Why it matters:** Tests that mock the unit under test prove nothing. Replacing inner-module mocks with real instances (in-memory DB, stub HTTP server, recorded fixtures) is often the single biggest testability win.
**Fix pattern:** Mock at the *boundary* only (outgoing HTTP, external APIs, time, randomness). Use `respx`/`nock`/`webmock` for HTTP, `freezegun`/`vi.useFakeTimers` for time. Replace inline module mocks with dependency injection at constructor boundaries.
</category>

<category name="auth-setup" priority="high">
**Signal:** E2E tests log in from scratch in every `beforeEach`, OR auth is skipped entirely, OR only public endpoints are tested.
**Why it matters:** Repeated login = slow, flaky, obscures real failures. No auth in tests = the authenticated path is untested.
**Fix pattern (Playwright):** `globalSetup.ts` that logs in once, saves `storageState.json`, referenced by `storageState` in `playwright.config.ts`. Multi-role: one storageState per role (`admin-state.json`, `user-state.json`).
**Fix pattern (API tests):** Shared `authenticated_client` fixture that gets a token once per session.
</category>

<category name="e2e-framework" priority="medium">
**Signal:** No `playwright.config.*`, `cypress.config.*`, no `e2e/` directory, no `pw-test` script in package.json.
**Why it matters:** Unit tests can't prove the full stack works. At least one e2e framework is required to reach score 7+.
**Fix pattern:** Playwright with TypeScript. One smoke test that loads the home page and checks for a known element. Grow from there. Do NOT add Cypress + Playwright — pick one.
</category>

<category name="e2e-coverage" priority="medium">
**Signal:** E2E framework exists but tests only cover homepage OR login; critical user flows (CRUD of main entity, payment flow, onboarding) are untested.
**Why it matters:** Framework without critical-path coverage is a false positive for testability.
**Fix pattern:** Identify the 3-5 critical user flows from SPEC.md. One e2e test per flow, end-to-end (not via API shortcuts). Page objects only if a selector is used in 3+ places — otherwise inline.
</category>

<category name="health-checks" priority="medium">
**Signal:** No `/health`, `/healthz`, `/api/health` endpoint. No docker `healthcheck:` stanza. Services don't expose "am I ready?" signal.
**Why it matters:** Without health checks, tests race against service startup and flake. CI has no reliable "ready" gate.
**Fix pattern:** `GET /health` returns `{status: "ok", db: "ok", ...}` with 200 OR 503. Check dependencies (DB ping, redis ping), not just "am I running".
</category>

<category name="api-contract-tests" priority="medium">
**Signal:** API routes tested via unit tests only (function-level), no HTTP-level tests, no OpenAPI/schema validation.
**Why it matters:** Unit tests miss serialization, auth middleware, validation errors, status codes.
**Fix pattern (Python):** `httpx.AsyncClient` or FastAPI `TestClient` hitting the real ASGI app. Assert status + JSON body schema.
**Fix pattern (JS/TS):** `supertest` against the app instance, OR Playwright's `request` fixture for pure API tests.
</category>

<category name="init-script" priority="medium">
**Signal:** `README.md` has a 10-step "Getting Started" section instead of one command. No `.outbid/init.sh`, no `make setup`, no `just bootstrap`.
**Why it matters:** Multi-step setup = reviewers don't run tests. An init script is the contract: "one command, then everything works."
**Fix pattern:** `.outbid/init.sh` (or `scripts/setup.sh`) that: starts services (docker-compose up -d), runs migrations, seeds data, creates test user, exports test credentials. Idempotent.
</category>

<category name="ci-parity" priority="low">
**Signal:** CI uses services locally-installed (apt install postgres) while devs use docker-compose, OR different Node/Python versions, OR CI runs tests local dev can't run.
**Why it matters:** CI-only failures waste hours. Local parity means faster diagnosis.
**Fix pattern:** Run the same `docker-compose.yml` in CI via `docker compose up -d` in a GitHub Actions step. Pin versions in one place (`.tool-versions`, `.nvmrc`, `.python-version`).
</category>

<category name="coverage-reporting" priority="low">
**Signal:** No coverage output, no coverage badge, no coverage gate in CI.
**Why it matters:** Coverage ≠ testability, but coverage *trends* flag regressions. A dropping number over time signals tests being deleted or skipped.
**Fix pattern:** `pytest --cov` or `vitest --coverage` producing `lcov.info`. Report to console in CI. **Do NOT set a coverage gate** (anti-pattern; see below).
</category>
</analysis-categories>

## Step 3: Score Each Recommendation

<scoring-rubric>
Anchor `current_score` to the harness. The 0-10 bands (from `run-init`'s rubric):

| Score | Label | State |
|---|---|---|
| 0-2 | Untestable | No dev server config, no test framework, no seed data, no health checks. Reviewer can only read code. |
| 3-4 | Minimal | Dev server starts but no auth, no seed data, no e2e framework. Curl-able public endpoints only. |
| 5-6 | Partial | Dev server + (some seed data OR auth), gaps remain. Some flows testable, not all. |
| 7-8 | Good | Dev server + auth + seed data + e2e framework. Reviewer can verify most features end-to-end. Minor gaps. |
| 9-10 | Excellent | Full stack, auth, rich seed data, e2e suite green, health checks, API contracts validated. |

**Score-impact heuristics** (approximate — use judgment):

| Moving from | To | Typical unlock |
|---|---|---|
| 0-2 → 3-4 | +2 | Working `commands.dev` + any test framework config |
| 3-4 → 5-6 | +1-2 | Seed data script OR auth setup |
| 5-6 → 7 | +1-2 | E2E framework + one smoke test |
| 7 → 8 | +1 | Critical-path e2e coverage (3-5 flows) |
| 8 → 9-10 | +1-2 | API contract tests, health checks, CI parity, multi-role auth |

Cap: `potential_score ≤ 10`. If sum of `score_impact`s would exceed 10 − current_score, trim the lowest-priority ones.
</scoring-rubric>

For each candidate gap, fill in:

- `category` — one of the categories above (use the exact name)
- `title` — imperative, ≤ 60 chars (e.g. "Add Playwright auth setup with storageState")
- `description` — 2-4 sentences: current state, proposed change, why it raises the score
- `effort` — `"small"` (<1h), `"medium"` (1-4h), `"large"` (>4h)
- `score_impact` — integer 0-3; the estimated score-band unlock from this single change
- `concrete_steps` — 3-6 bullets. Each bullet names a file to create OR a specific code change. No vague advice.

Sort by `score_impact` DESC, then by `effort` ASC (cheap-and-impactful first).

## Step 4: Write testability-recommendations.json

<output file="${DIRIGENT_RUN_DIR}/testability-recommendations.json">
{
  "current_score": 5,
  "potential_score": 9,
  "baseline_summary": "1-2 sentence restatement of testability_description from the harness",
  "recommendations": [
    {
      "category": "auth-setup",
      "title": "Add Playwright auth setup with storageState",
      "description": "E2E tests currently log in from scratch in every beforeEach, which is slow and flaky. A globalSetup.ts that logs in once and saves browser state means all e2e tests run authenticated. Raises e2e-framework score by removing the biggest source of e2e flakes.",
      "effort": "small",
      "score_impact": 2,
      "concrete_steps": [
        "Create e2e/global-setup.ts with login flow using test credentials from seed",
        "Add `globalSetup: './e2e/global-setup.ts'` and `use.storageState: '.e2e/auth-state.json'` to playwright.config.ts",
        "Add `.e2e/auth-state.json` to .gitignore",
        "Ensure seed script creates the test user globalSetup expects"
      ]
    },
    {
      "category": "seed-data",
      "title": "Add comprehensive seed script with edge-case data",
      "description": "Current seed is empty or minimal, so tests pass on empty DBs trivially. Adding roles + sample records + edge-case rows lets tests prove behavior under realistic conditions.",
      "effort": "medium",
      "score_impact": 1,
      "concrete_steps": [
        "Create scripts/seed.ts (or prisma/seed.ts) referenced from package.json",
        "Add 3 users: admin, regular, viewer",
        "Add 5-10 sample records for each main entity from SPEC",
        "Add edge-case rows: empty strings, nulls, max-length, unicode, boundary dates",
        "Wire into .outbid/init.sh (or equivalent) so reviewers get it for free"
      ]
    }
  ]
}
</output>

## Rules

<rules>
<rule>`current_score` MUST equal `test-harness.json`'s `testability_score` — do not re-score from scratch</rule>
<rule>Every recommendation MUST have `concrete_steps` naming specific files/configs/code paths. "Improve tests" is not a step; "Create e2e/global-setup.ts" is.</rule>
<rule>`effort` is one of: `"small"` (<1h), `"medium"` (1-4h), `"large"` (>4h). Pick by how long an experienced dev would need on this stack.</rule>
<rule>`score_impact` is an integer 0-3. Use the score-band heuristics in the rubric — don't inflate to justify the recommendation.</rule>
<rule>`potential_score = current_score + sum(score_impacts)`, capped at 10. If the sum would exceed 10 − current_score, drop low-priority recommendations.</rule>
<rule>Sort recommendations by `score_impact` DESC, tie-break by `effort` ASC.</rule>
<rule>Prefer boundary mocks (HTTP, time, external APIs) over module-internal mocks. If you recommend adding mocks, specify the boundary.</rule>
<rule>Match recommendations to the existing stack. pytest project → pytest fixtures. Vitest project → vitest setup. Do not suggest switching frameworks unless the current one is broken.</rule>
<rule>If `current_score` is already 8+, focus on edge-case coverage, multi-role auth, API contract validation — NOT on adding more infra.</rule>
<rule>Do not re-propose anything already in `testability_description` or `testability_rationale`. Read those fields first.</rule>
<rule>Prioritize recommendations that unblock the SPEC's main feature area — if SPEC is "add payment flow" and there's no e2e for checkout, that's higher priority than a generic health-check addition.</rule>
<rule>Query context7 for framework config syntax before writing stack-specific `concrete_steps` — Playwright/pytest/vitest APIs change between versions.</rule>
<rule>`baseline_summary` is informational (human-readable one-liner); the executor only reads `current_score`, `potential_score`, and `recommendations[]`. Keep it short.</rule>
</rules>

## Anti-Patterns (do NOT recommend these)

<anti-patterns>
<anti-pattern name="100-percent-coverage-goal">
**Never** recommend "reach X% coverage" as a goal. Coverage is a lagging indicator, not a target. Tests written to hit a number are usually worthless.
</anti-pattern>

<anti-pattern name="mock-everything">
**Never** recommend replacing real dependencies with mocks as a testability improvement. Mocking the thing under test is the opposite of testability. Mock only at system boundaries (outgoing HTTP, time, randomness, 3rd-party APIs).
</anti-pattern>

<anti-pattern name="add-tests-for-coverage">
**Never** recommend "add more unit tests" without specifying what property those tests prove. Tests must have a claim. "Test the UserService" is not a claim; "Test that UserService.delete is idempotent" is.
</anti-pattern>

<anti-pattern name="coverage-gate">
**Never** recommend a CI coverage gate (e.g., "fail if coverage < 80%"). Gates push devs to write no-op tests. Coverage reporting (trend visibility) is fine; gating is not.
</anti-pattern>

<anti-pattern name="test-pyramid-religion">
**Never** recommend shifting a test from integration to unit "because the pyramid says so". Write the test at the level where the bug would be caught cheapest. Integration tests that prove real behavior beat unit tests that prove a mock's behavior.
</anti-pattern>

<anti-pattern name="dual-framework">
**Never** recommend adding Cypress when Playwright exists (or vice versa). Pick one. Two e2e frameworks doubles the maintenance and halves the team's expertise.
</anti-pattern>

<anti-pattern name="snapshot-everything">
**Never** recommend snapshot tests for structural output (HTML, JSON) as a testability improvement. Snapshots rot silently; tests that assert specific invariants don't.
</anti-pattern>

<anti-pattern name="flaky-tolerated">
**Never** recommend retries (`retry: 3`) as a fix for flaky tests. Retries hide real bugs. Fix the flake's root cause (usually: no health check, no auth reuse, no seed isolation).
</anti-pattern>
</anti-patterns>

## Integration

- **Input:** `${DIRIGENT_RUN_DIR}/test-harness.json` (produced by `run-init`)
- **Output:** `${DIRIGENT_RUN_DIR}/testability-recommendations.json`
- **Next consumer:** `create-plan` reads this file and generates tasks. Each recommendation typically becomes one task (or one phase for `effort: "large"` items).
- **Downstream:** Executor runs the tasks. After execution, a subsequent `run-init` should show `testability_score` moved toward `potential_score`.

## Constraints

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary in the file</constraint>
<constraint>File path MUST be `${DIRIGENT_RUN_DIR}/testability-recommendations.json`</constraint>
<constraint>JSON must parse. Validate before finishing.</constraint>
<constraint>Max 10 recommendations. If you find more, drop the lowest-impact ones — the planner can't absorb a 20-item backlog in one phase.</constraint>
<constraint>Time budget: 10 minutes. This is analysis, not implementation.</constraint>
</constraints>
