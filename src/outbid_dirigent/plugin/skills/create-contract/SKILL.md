---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
context: fork
agent: contract-negotiator
---

# Create Phase Contract

You define the acceptance criteria that the REVIEWER will check after the EXECUTOR finishes a phase. The criteria you write are the definition of "done" — if they pass, the phase ships. If they fail, the executor has to fix.

## ⛔ MANDATORY JSON SCHEMA — Your output MUST match this EXACTLY

The output file is validated by Pydantic. **Any deviation = silent rejection.** Use EXACTLY these field names:

```json
{
  "phase_id": "01",
  "phase_name": "Phase Name",
  "objective": "One sentence: what this phase achieves",
  "acceptance_criteria": [
    {
      "id": "AC-{PHASE_ID}-01",
      "description": "What must be true",
      "verification": "Run: <executable command>",
      "layer": "structural|behavioral|boundary"
    }
  ],
  "quality_gates": ["All new/modified files compile without errors", "No regressions in existing functionality", "Code follows project conventions"],
  "out_of_scope": ["What this phase does NOT cover"],
  "expected_files": [{"path": "src/foo.py", "change": "Add new class"}]
}
```

**Hard constraints enforced by Pydantic validation:**
- Field name is `acceptance_criteria` — NOT `criteria`, NOT `tests`, NOT `checks`
- Field name is `objective` — NOT `description`, NOT `verification_strategy`
- Field name is `verification` — NOT `verify`, NOT `command`, NOT `check`
- Each criterion `id` format: `AC-{PHASE_ID}-{NN}` (e.g., AC-01-01) — NOT S01, B01, etc.
- Each `verification` MUST start with `"Run: "` followed by an executable shell command
- `layer` must be one of: `"structural"`, `"behavioral"`, `"boundary"`
- Min 1, **max 8** criteria total (Pydantic rejects >8)
- Max 2 structural, min 3 behavioral, min 1 boundary

---

## The Three-Layer Testing Pyramid

Every contract MUST contain criteria from three layers:

### Layer 1: STRUCTURAL (max 2, ~20%)

Quick sanity checks — does the code compile, are files in place?

**Purpose:** Catch obvious build breaks before wasting time on behavioral tests.

**Examples:**
- `"Run: npm run build"` — project compiles
- `"Run: python -m py_compile src/routes/users.py"` — new file is valid Python
- `"Run: npx tsc --noEmit"` — TypeScript type-checks

**Limit:** Max 2 structural criteria per contract. These are not the substance.

### Layer 2: BEHAVIORAL (min 3, ~60%)

The feature WORKS when a user exercises it. This is the core of the contract.

**Purpose:** Prove the feature does what the spec says by actually running it.

**Format:** Given/When/Then, verified by executable commands against the running system.

**Examples:**
```
Given: authenticated admin user
When:  GET /api/tenants/1/settings
Then:  HTTP 200 with JSON containing all settings fields

Verification: Run: curl -sf http://localhost:3000/api/tenants/1/settings \
  -H "Authorization: Bearer $(curl -sf http://localhost:3000/api/auth/login \
  -d '{"email":"admin@test.com","password":"test123"}' | jq -r .token)" \
  | jq 'keys | length >= 5'
```

**What behavioral criteria MUST test:**
- Request/response correctness (right status code, right response body)
- Auth enforcement (authenticated users succeed, unauthenticated fail)
- Data persistence (write then read back — does the value stick?)
- Integration (does the frontend actually consume the new API field?)

### Layer 3: BOUNDARY (min 1, ~20%)

Error paths and edge cases — what happens when things go wrong?

**Purpose:** Prove the system handles bad input, missing data, and unauthorized access gracefully.

**Examples:**
```
Given: no authentication
When:  GET /api/admin/users
Then:  HTTP 401 or 403

Verification: Run: HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  http://localhost:3000/api/admin/users); test "$HTTP_CODE" = "401" -o "$HTTP_CODE" = "403"
```

```
Given: valid auth, nonexistent resource
When:  GET /api/tenants/999999/settings
Then:  HTTP 404

Verification: Run: curl -s -o /dev/null -w '%{http_code}' \
  http://localhost:3000/api/tenants/999999/settings \
  -H "Authorization: Bearer $TOKEN" | grep -q 404
```

---

## BANNED Verification Patterns

These test CODE STRUCTURE, not USER BEHAVIOR. They are **forbidden** in behavioral and boundary criteria:

| Pattern | Why it's bad | What to use instead |
|---------|-------------|-------------------|
| `grep "def func" src/file.py` | Proves string exists in source, not that func works | `curl` the endpoint that calls `func` |
| `test -f src/routes/users.py` | File existing ≠ feature working | `curl /api/users` and check response |
| `cat src/config.py \| grep SETTING` | Reads source, not runtime behavior | Hit an endpoint that uses the setting |
| `wc -l src/models.py` | Line count says nothing about correctness | Test the model via API CRUD |
| `rg "router.include" src/main.py` | Registration ≠ working endpoint | `curl` the registered route |

**The litmus test:** "If this verification passes, would a USER notice?" If no, it's structural, not behavioral.

---

## Step 1: Read Context

1. **Required:** `.dirigent/PLAN.json` — find the phase matching `$ARGUMENTS` (the phase ID)
2. **Required:** `.dirigent/SPEC.md` — understand what the user wants
3. **Critical:** `.dirigent/test-harness.json` — if this exists, it tells you EXACTLY how to verify

## Step 2: Build Verification Commands

### If test-harness.json EXISTS (preferred path)

You MUST use these fields:

| Harness Field | How to Use |
|--------------|-----------|
| `base_url` | Base for ALL curl commands (e.g., `curl -sf {base_url}/api/users`) |
| `auth.login_command` | Get a token/session BEFORE authenticated tests |
| `seed.users` | Reference test users in criteria (email, role, password) |
| `verification_commands` | Use at least one directly as a criterion verification |
| `e2e_framework.run_command` | At least one criterion MUST use this if framework ≠ "none" |
| `health_checks` | Use one as a structural criterion (system is alive) |

**Example flow for an authenticated endpoint test:**
```bash
# Step 1: Get auth token using harness login_command
TOKEN=$(curl -sf http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"test123"}' | jq -r .token)

# Step 2: Hit the endpoint under test
curl -sf http://localhost:3000/api/tenants/1/settings \
  -H "Authorization: Bearer $TOKEN" | jq .default_currency
```

Combine both into a single verification command using `&&` or subshells.

### If NO test-harness.json (fallback)

Use the project's test runner for behavioral verification:

- **Python:** `Run: cd {repo} && python -m pytest tests/test_feature.py -v -k "test_name"`
- **Node:** `Run: cd {repo} && npx jest --testPathPattern="feature" --verbose`
- **Go:** `Run: cd {repo} && go test ./pkg/feature/... -v -run TestName`

Write behavioral criteria that map to specific test functions. If no tests exist yet, write criteria that use the framework's test client:

```
Run: cd {repo} && python -c "
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
resp = client.get('/api/users', headers={'Authorization': 'Bearer test'})
assert resp.status_code == 200
assert len(resp.json()) > 0
"
```

## Step 3: Write the Contract

Write `.dirigent/contracts/phase-{PHASE_ID}.json`:

```json
{
  "phase_id": "01",
  "phase_name": "User Management API",
  "objective": "Implement CRUD endpoints for user management with role-based access",
  "acceptance_criteria": [
    {
      "id": "AC-01-01",
      "description": "Project compiles and lints without errors",
      "verification": "Run: npm run build && npm run lint",
      "layer": "structural"
    },
    {
      "id": "AC-01-02",
      "description": "GET /api/users returns a list of users with id, email, and role fields",
      "verification": "Run: TOKEN=$(...login...) && curl -sf http://localhost:3000/api/users -H \"Authorization: Bearer $TOKEN\" | jq '.[0] | has(\"id\", \"email\", \"role\")'",
      "layer": "behavioral"
    },
    {
      "id": "AC-01-03",
      "description": "POST /api/users creates a user and returns it with a generated ID",
      "verification": "Run: TOKEN=$(...) && curl -sf -X POST http://localhost:3000/api/users -H \"Authorization: Bearer $TOKEN\" -H \"Content-Type: application/json\" -d '{\"email\":\"new@test.com\",\"role\":\"viewer\"}' | jq '.id'",
      "layer": "behavioral"
    },
    {
      "id": "AC-01-04",
      "description": "Data persists: POST then GET returns the created user",
      "verification": "Run: TOKEN=$(...) && ID=$(curl -sf -X POST .../api/users ... | jq -r .id) && curl -sf .../api/users/$ID -H ... | jq '.email' | grep -q 'new@test.com'",
      "layer": "behavioral"
    },
    {
      "id": "AC-01-05",
      "description": "Viewer role cannot access admin endpoints — returns 403",
      "verification": "Run: VIEWER_TOKEN=$(...login as viewer...) && HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/api/admin/users -H \"Authorization: Bearer $VIEWER_TOKEN\") && test \"$HTTP_CODE\" = \"403\"",
      "layer": "boundary"
    },
    {
      "id": "AC-01-06",
      "description": "POST with duplicate email returns 409 Conflict",
      "verification": "Run: TOKEN=$(...) && curl -s -o /dev/null -w '%{http_code}' -X POST .../api/users -H ... -d '{\"email\":\"admin@test.com\",\"role\":\"viewer\"}' | grep -q 409",
      "layer": "boundary"
    }
  ],
  "quality_gates": [
    "All new/modified files compile without errors",
    "No regressions in existing functionality",
    "Code follows project conventions"
  ],
  "out_of_scope": ["User profile editing", "Password reset flow"],
  "expected_files": [
    {"path": "src/routes/users.py", "change": "New CRUD route handlers"},
    {"path": "src/models/user.py", "change": "User model definition"}
  ]
}
```

## Rules

<rules>
<rule>Min 3 behavioral criteria, min 1 boundary criterion, max 2 structural criteria</rule>
<rule>Max 8 criteria total per contract</rule>
<rule>Every behavioral/boundary criterion verification MUST start with "Run: " followed by an executable command</rule>
<rule>NEVER use grep/rg/cat on source files as behavioral verification — test the RUNNING system</rule>
<rule>If test-harness.json exists, you MUST use its base_url and auth in verification commands</rule>
<rule>Criteria come from the phase's task descriptions — what do the tasks promise to deliver?</rule>
<rule>The executor will read these criteria and their verification commands — be precise about expected behavior</rule>
<rule>Each criterion answers: "If this fails, would a user notice?" If no, it belongs in structural, not behavioral</rule>
<rule>ID format: AC-{PHASE_ID}-{NN} (e.g., AC-01-01, AC-01-02)</rule>
<rule>Output MUST be valid JSON matching the schema exactly</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>File path MUST be .dirigent/contracts/phase-{PHASE_ID}.json</constraint>
</constraints>

## Validation (MANDATORY)

After writing the JSON file, validate it:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py .dirigent/contracts/phase-$ARGUMENTS.json
```

If validation fails, read the error messages, fix the JSON, and re-run until it passes.
