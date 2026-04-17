---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
context: fork
agent: contract-negotiator
---

# Create Phase Contract

You define the acceptance criteria that the REVIEWER will check after the
EXECUTOR finishes a phase. These criteria are the definition of "done" — if
they pass, the phase ships. If they fail, the executor has to fix.

## The one rule that matters

**Every criterion describes something a user (or, on pre-UI phases, a calling
subsystem) can observe.** Not "the API returned 200." Not "the function exists."
What the user sees, types, clicks, or is blocked from doing.

If a criterion passes and a real user would notice no difference in their
experience, the criterion tested the wrong thing.

## Step 1: Read the SPEC's user outcome

1. Read `${DIRIGENT_RUN_DIR}/SPEC.md`. Find the statements about what the user
   can do or see when this feature is done — the "User Outcome." Look for any
   section serving this purpose, regardless of heading or language:
   `## User Outcome`, `## Success Criteria`, `## Acceptance`, `## Definition
   of Done`, `## Erfolgreich wenn`, `## Success`, `## The prototype is
   successful when...`, or a narrative intro that explicitly describes the
   user perspective. Different specs phrase this differently — the semantic
   test is "does this section say what the user can do / see / experience
   when the feature ships?" If yes, it IS the anchor.
2. Only if no such section or near-equivalent exists, synthesize one from
   the Goal and Requirements and write it back to SPEC.md under a `## User
   Outcome` heading. Do NOT duplicate an existing anchor — writing a
   near-identical English section below a German one (or vice versa) creates
   redundancy and looks like the skill didn't read the spec properly.
3. Every criterion you write must map back to one of those user-outcome
   statements. If you can't map it, it's probably testing plumbing the user
   doesn't care about.

## Step 2: Read the phase kind

The planner already classified the phase. Read `phase.kind` for this
phase from `${DIRIGENT_RUN_DIR}/PLAN.json` and copy it into the contract
as `phase_kind`. One of:

| Phase kind | Meaning | Examples |
|---|---|---|
| `user-facing` | Delivers a UI surface or user-observable behavior change. | "Admin can manage users", "Add dark mode toggle", "Checkout flow" |
| `integration` | Delivers a subsystem that a later phase will expose to users. | "Auth middleware", "tRPC router scaffold", "Background job queue" |
| `infrastructure` | Scaffolding, migrations, tooling, CI. No consumer within the run. | "Scaffold Next.js app", "Prisma schema + initial migration" |

**If the plan does not have `kind` on the phase** (legacy plan, missing field):
classify it yourself using the table above and record the choice in the
contract. Prefer `user-facing` in doubt — greenfield scaffolds often still
have a trivial user-visible surface (dev server serves default page) that
proves more than a bare `typecheck passes`.

**Do not contradict the planner.** If the plan says `user-facing` but there's
no user-observable work in the phase tasks, that's a planning bug — surface
it as a finding (a DEVIATION note in your output), do not silently reclassify.

The contract validator enforces layer quotas based on `phase_kind`, and
the final phase cannot be classified `infrastructure`.

## The four layers

### `structural` — does it build and start?
Compile, lint, typecheck, subsystem liveness. Quick sanity, not the substance.

### `unit` — does the new logic do what it claims in isolation?
Fast, deterministic tests for pure logic added in this phase (validators,
transformers, state machines, business rules). Scoped to the files this phase
touches — not the whole suite.

### `user-journey` — the main layer (was: `behavioral`)
A user does something and observes something. Written as a short narrative,
verified end-to-end through the real UI when possible.

**Good description shape:**
- "After logging in, the admin sees the User Management link in the sidebar."
- "When a user types an invalid email and submits, they see 'Please enter a
  valid email' below the field."
- "On opening the dashboard, the manager sees three cards showing total users,
  active users, and disabled users."

**Bad description shape:**
- "GET /api/x returns 200 with field y."
- "The `users` table has a `created_at` column."
- "The POST handler validates the payload."

For `integration` phases with no UI yet, "user" means the calling subsystem —
the criterion describes a contract the caller relies on.

### `edge-case` — the user is wrong or the system is degraded (was: `boundary`)
The user submits bad data, has no permission, or hits a missing resource, and
sees something they can act on.

**Good:** "When the admin submits a form with an email already registered,
they see 'This email is already in use' near the email field and the form
stays open."

**Bad:** "POST returns 409."

## Layer quotas by phase kind

| Phase kind | structural | unit | user-journey | edge-case | total |
|---|---|---|---|---|---|
| `user-facing` | max 2 | min 1 *(warn-only: when the phase adds pure logic)* | min 3 | min 1 | max 8 |
| `integration` | max 2 | min 2 | min 2 *(as contract probes)* | min 1 | max 8 |
| `infrastructure` | min 1, max 3 | — | — | — | max 3 |

**Final-phase rule:** if this is the highest-numbered phase in PLAN.json, at
least one `user-journey` criterion must exercise the full e2e framework
(Playwright/Cypress/Detox/pytest --e2e) against the running system. Final
phases cannot be classified `infrastructure` — if the run's last phase has no
user-visible delivery, the plan is wrong.

## Step 3: Build verification commands

Match the tool to what the criterion claims to test.

### For `user-journey` and `edge-case` on `user-facing` phases
Playwright (or the project's configured e2e framework) is the default. Never curl.

```
Run: npx playwright test --grep "admin adds user inline" --reporter=line
```

The Playwright spec file is a deliverable of the phase — the executor writes
it alongside the implementation. Reference the test name in your criterion's
`description` so the connection is obvious ("The admin clicks 'Add User'..." →
spec file named `admin-adds-user-inline.spec.ts`).

### For `user-journey` and `edge-case` on `integration` phases
curl + jq is legitimate. The "user" here is a calling subsystem; the contract
probe is the equivalent of a UI interaction.

```
Run: TOKEN=$(curl -sf -X POST http://localhost:3000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@test.com","password":"test123"}' | jq -r .token) && \
  curl -sfH "Authorization: Bearer $TOKEN" http://localhost:3000/api/me | \
  jq -e '.email == "admin@test.com"'
```

If `test-harness.json` specifies `auth.login_command` and `base_url`, use them
verbatim — don't hand-roll login flows.

### For `unit`
The project's unit test runner, scoped to files added in this phase:

```
Run: pnpm test -- src/users/validators.test.ts --run --reporter=default
Run: python -m pytest tests/unit/test_users.py -v
Run: go test ./internal/users -run TestUserValidator
```

Scope the command so the reviewer can tell which tests the criterion gates. A
phase-wide `pnpm test` is too coarse — a regression in another module would
silently fail this criterion.

### For `structural`
Build, lint, typecheck, migrate, dev-server-starts. One command per criterion:

```
Run: npm run build
Run: pnpm typecheck
Run: pnpm prisma migrate status | grep -q 'up to date'
Run: (npm run dev &) && sleep 4 && curl -sf http://localhost:3000/
```

### If `test-harness.json` exists, use it

| Harness field | How to use |
|---|---|
| `base_url` | Base for curl / Playwright `page.goto` |
| `auth.login_command` | Run before authenticated criteria |
| `seed.users` | Reference by email/role in descriptions |
| `e2e_framework.run_command` | Every user-facing phase MUST use this for user-journey criteria |
| `health_checks` | One may become a structural criterion |

### If `test-harness.json` reports `e2e_framework: "none"`

On `user-facing` phases: fall back to curl-shaped `user-journey` criteria AND
add this to `quality_gates`: `"No e2e framework configured — user-journey
criteria verified indirectly via API; invest in Playwright before shipping to
real users."`

## Banned verification patterns

These test the wrong thing. Forbidden on the layers shown.

| Pattern | Banned on | Why | Use instead |
|---|---|---|---|
| `grep "def func" src/file.py` | all layers | String in source ≠ func works | Exercise the function through its real caller |
| `test -f src/routes/users.py` | all layers | File existing ≠ feature working | Hit the feature the file implements |
| `wc -l src/models.py` | all layers | Line count says nothing | Test the model through its caller |
| `curl ... \| grep '"status":"ok"'` | user-journey, edge-case on `user-facing` | Server replied, not that any user saw anything | Playwright: navigate, assert visible text |
| `jq '.id'` as "feature works" | user-journey, edge-case on `user-facing` | Response shape ≠ user experience | Playwright: create via UI, assert the row renders |
| `test "$HTTP_CODE" = "403"` | edge-case on `user-facing` | Status codes are invisible to users | Playwright: navigate, assert "access denied" UI |
| `pnpm test` (no file scope) | unit | A regression in another module silently fails this | Scope to files this phase touches |

The litmus test on `user-facing` phases: *"If this verification passes, would
a USER notice something is working?"* If no, it's the wrong layer or the
wrong tool.

## Step 4: Write the contract

Write `${DIRIGENT_RUN_DIR}/contracts/phase-{PHASE_ID}.json`:

```json
{
  "phase_id": "04",
  "phase_name": "User Management",
  "phase_kind": "user-facing",
  "objective": "An admin can add, edit, and disable users and see the results immediately on screen",
  "acceptance_criteria": [
    {
      "id": "AC-04-01",
      "description": "Project compiles and the admin area is reachable",
      "verification": "Run: npm run build && (npm run dev &) && sleep 4 && curl -sf http://localhost:3000/admin",
      "layer": "structural"
    },
    {
      "id": "AC-04-02",
      "description": "The user-form validator rejects empty email, invalid email format, and emails over 254 chars; accepts RFC-compliant emails",
      "verification": "Run: pnpm test -- src/users/validators.test.ts --run",
      "layer": "unit"
    },
    {
      "id": "AC-04-03",
      "description": "After logging in as admin and opening User Management, the admin sees existing users listed with email and role",
      "verification": "Run: npx playwright test --grep 'admin sees user list' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-04",
      "description": "The admin clicks 'Add User', fills email + role, submits, and sees the new row appear in the table without a page reload",
      "verification": "Run: npx playwright test --grep 'admin adds user inline' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-05",
      "description": "The admin changes a user's role and saves; the row updates in place and persists across reload",
      "verification": "Run: npx playwright test --grep 'admin edits role persists' --reporter=line",
      "layer": "user-journey"
    },
    {
      "id": "AC-04-06",
      "description": "When the admin submits a duplicate email, they see 'This email is already registered' next to the email field and the form stays open",
      "verification": "Run: npx playwright test --grep 'duplicate email inline error' --reporter=line",
      "layer": "edge-case"
    }
  ],
  "quality_gates": [
    "All new/modified files compile without errors",
    "No regressions in existing functionality",
    "Code follows project conventions"
  ],
  "out_of_scope": ["Password reset flow", "Bulk user import"],
  "expected_files": [
    {"path": "src/users/validators.ts", "change": "Email and role validators"},
    {"path": "src/users/validators.test.ts", "change": "Unit tests for validators"},
    {"path": "src/app/admin/users/page.tsx", "change": "User management screen"},
    {"path": "tests/e2e/admin-users.spec.ts", "change": "Playwright specs for user-journey criteria"}
  ]
}
```

## Worked examples for other phase kinds

### `integration` phase: "Auth layer"

```json
{
  "phase_id": "02",
  "phase_kind": "integration",
  "objective": "Downstream features can require and receive an authenticated session",
  "acceptance_criteria": [
    {
      "id": "AC-02-01",
      "description": "Project compiles and auth routes are registered",
      "verification": "Run: npm run build && curl -sf http://localhost:3000/api/auth/providers",
      "layer": "structural"
    },
    {
      "id": "AC-02-02",
      "description": "Session-token verifier accepts a freshly signed token and rejects a tampered one",
      "verification": "Run: pnpm test -- src/auth/session.test.ts --run",
      "layer": "unit"
    },
    {
      "id": "AC-02-03",
      "description": "Role-guard middleware admits admin role for /api/admin and rejects viewer",
      "verification": "Run: pnpm test -- src/auth/role-guard.test.ts --run",
      "layer": "unit"
    },
    {
      "id": "AC-02-04",
      "description": "A sign-in request with valid credentials returns a usable session token that downstream handlers can verify",
      "verification": "Run: TOKEN=$(curl -sf -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"admin@test.com\",\"password\":\"test123\"}' | jq -r .token) && curl -sfH \"Authorization: Bearer $TOKEN\" http://localhost:3000/api/me | jq -e '.email == \"admin@test.com\"'",
      "layer": "user-journey"
    },
    {
      "id": "AC-02-05",
      "description": "A request without a valid token is rejected — downstream handlers can rely on authentication being enforced",
      "verification": "Run: HTTP=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/me) && test \"$HTTP\" = \"401\"",
      "layer": "user-journey"
    },
    {
      "id": "AC-02-06",
      "description": "A sign-in attempt for a disabled account is rejected",
      "verification": "Run: HTTP=$(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"disabled@test.com\",\"password\":\"test123\"}') && echo $HTTP | grep -qE '40[13]'",
      "layer": "edge-case"
    }
  ],
  "out_of_scope": ["Login UI", "Password reset"],
  "expected_files": [
    {"path": "src/auth/session.ts", "change": "Token issue/verify"},
    {"path": "src/auth/session.test.ts", "change": "Unit tests for session logic"},
    {"path": "src/auth/role-guard.ts", "change": "Role-based middleware"},
    {"path": "src/auth/role-guard.test.ts", "change": "Unit tests for role guard"}
  ]
}
```

*No Playwright here — this phase has no UI. The next phase that exposes a
login screen writes real user-journey criteria via Playwright.*

### `infrastructure` phase: "Scaffold Next.js + Prisma"

```json
{
  "phase_id": "01",
  "phase_kind": "infrastructure",
  "objective": "The base app scaffold is in place; the dev server runs; migrations apply cleanly",
  "acceptance_criteria": [
    {
      "id": "AC-01-01",
      "description": "Project installs and type-checks without errors",
      "verification": "Run: pnpm install && pnpm typecheck",
      "layer": "structural"
    },
    {
      "id": "AC-01-02",
      "description": "Prisma migrations apply against a clean database",
      "verification": "Run: pnpm prisma migrate reset --force --skip-seed && pnpm prisma migrate status | grep -q 'Database schema is up to date'",
      "layer": "structural"
    },
    {
      "id": "AC-01-03",
      "description": "The dev server starts and the default page is served at /",
      "verification": "Run: (pnpm dev &) && sleep 5 && curl -sf http://localhost:3000/ | grep -q '<html'",
      "layer": "structural"
    }
  ],
  "out_of_scope": ["Any user-facing screens", "Business logic"],
  "expected_files": [
    {"path": "package.json", "change": "Dependencies and scripts"},
    {"path": "prisma/schema.prisma", "change": "Initial schema"}
  ]
}
```

*All `structural` — scaffolding has no user-journey. The liveness probe
(`curl /`) counts as structural because it proves the subsystem is alive, not
that any user interaction succeeded.*

## Rules

<rules>
<rule>Every criterion's `description` must read as user intent (or, on integration phases, calling-subsystem intent) — not as implementation detail. If removing the word "user" from the description breaks the sentence, you're writing it right.</rule>
<rule>Every criterion must map to a User Outcome statement in SPEC.md. Check for an existing anchor first — "User Outcome", "Success Criteria", "Definition of Done", "Erfolgreich wenn", or any narrative section that describes the user perspective in any language. Only synthesize and write back if no equivalent exists. Never create a duplicate anchor.</rule>
<rule>`phase_kind` is required. One of: `user-facing`, `integration`, `infrastructure`.</rule>
<rule>Layer quotas by phase_kind (enforced by validator):
  - `user-facing`: max 2 structural, min 3 user-journey, min 1 edge-case; min 1 unit STRONGLY recommended when the phase adds pure logic (validator warns if 0).
  - `integration`: max 2 structural, min 2 unit, min 2 user-journey (as contract probes), min 1 edge-case.
  - `infrastructure`: min 1 structural, max 3 structural, zero of everything else. Total max 3.</rule>
<rule>`user-facing` and `integration` phases: max 8 criteria total. `infrastructure`: max 3 total.</rule>
<rule>Every `verification` MUST start with `Run: ` followed by an executable shell command.</rule>
<rule>On `user-facing` phases, `user-journey` and `edge-case` verifications MUST use the project's e2e framework (Playwright/Cypress/Detox/pytest --e2e). curl/jq is forbidden for these layers on user-facing phases.</rule>
<rule>On `integration` phases, `user-journey` criteria may use curl/jq — the "user" is a calling subsystem, not a human.</rule>
<rule>On the final phase (highest-numbered in PLAN.json), at least one user-journey criterion MUST use the project's e2e framework end-to-end. The final phase cannot be classified `infrastructure`.</rule>
<rule>`unit` verifications MUST be scoped to files this phase adds or modifies — not the whole suite.</rule>
<rule>E2e criterion descriptions MUST describe user-observable behavior, not test-runner output ("user can X", not "tests pass").</rule>
<rule>`objective` frames the user (or on integration phases, the calling subsystem) as the subject of a capability. Good shapes: "An admin can manage users...", "A staff user can scan a token and see the outcome...", "The coordinator sees live entry counts...". Do NOT start with system-perspective verbs: no "Implement", "Build", "Create", "Add", "Set up". If the first word is a verb at all, it names something the user does, not something the developer does.</rule>
<rule>Each criterion answers: "If this fails, would a user notice?" If no on a `user-facing` phase, it belongs in `structural` or the layer is wrong.</rule>
<rule>ID format: `AC-{PHASE_ID}-{NN}` (e.g., AC-04-01).</rule>
<rule>`expected_files` must include any new test files (e2e specs, unit test files) — the reviewer uses this for scope checks and the executor treats it as a deliverable list.</rule>
<rule>The executor will read these criteria and their verification commands — be precise about expected behavior.</rule>
<rule>Output MUST be valid JSON matching the schema exactly.</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>File path MUST be ${DIRIGENT_RUN_DIR}/contracts/phase-{PHASE_ID}.json</constraint>
</constraints>

## Validation (MANDATORY)

After writing the JSON file, validate it:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py ${DIRIGENT_RUN_DIR}/contracts/phase-$ARGUMENTS.json
```

If validation fails, read the error messages, fix the JSON, and re-run until it passes.
