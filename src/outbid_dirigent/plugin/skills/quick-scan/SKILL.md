---
name: quick-scan
description: Quick scan of relevant files for a feature (Hybrid route)
context: fork
agent: infra-architect
---

# Quick Scan

You identify the **minimal set of files** relevant to the feature described in `${DIRIGENT_RUN_DIR}/SPEC.md` and write `${DIRIGENT_RUN_DIR}/CONTEXT.md` for the planner to consume.

This is the Hybrid route's distinguishing step — the sweet-spot between Greenfield (no prior code) and Legacy (extract every rule). The repo is mid-size and only a slice is relevant. Read that slice **smart**, not all.

Your output is the planner's fuel: if you miss the entry point, the plan will route tasks to the wrong files. If you dump the whole repo, the planner drowns in tokens and writes bad tasks.

## When This Runs

Hybrid route, after `run-init`. You have:
- `${DIRIGENT_RUN_DIR}/SPEC.md` — what's being built
- `${DIRIGENT_RUN_DIR}/test-harness.json` — build/test/run commands (from init)
- The live repo — read it selectively

You are consumed by `create-plan`, which reads `${DIRIGENT_RUN_DIR}/CONTEXT.md` at Step 1 and uses it to skip generic repo analysis.

## Steps At A Glance

| # | Step | Output |
|---|---|---|
| 1 | Read SPEC and pull feature keywords | Keyword list in memory |
| 2 | Grep by feature name + related terms | Candidate file list |
| 3 | Identify entry points and follow imports (depth ≤ 2) | Entry points + direct deps |
| 4 | Find nearest sibling feature (pattern reference) | 1-2 files to mirror |
| 5 | Classify: modify vs. read-only vs. ignore | Triaged file list |
| 6 | Extract 2-4 pattern snippets | Snippets in memory |
| 7 | Write CONTEXT.md | `${DIRIGENT_RUN_DIR}/CONTEXT.md` |
| 8 | Validate size budget | Under token ceiling |

No commit. CONTEXT.md is transient planner fuel in `${DIRIGENT_RUN_DIR}`, not repo content.

## Step 1: Extract Feature Keywords from SPEC

Read `${DIRIGENT_RUN_DIR}/SPEC.md`. Pull two kinds of terms:

- **Feature name tokens** — nouns and verbs from the feature title (e.g. "password reset" → `password`, `reset`, `forgot`)
- **Domain/adjacent terms** — entities and actions mentioned in the SPEC body (e.g. `user`, `email`, `token`, `expiry`)

Write these as a mental list. You will use them in Step 2.

## Step 2: Grep by Feature Name and Related Terms

Search in this order — stop as soon as you have a clear entry point:

1. **Exact feature name.** `rg -l "password_reset|PasswordReset|forgotPassword"` — case variants covering snake, Pascal, and camel.
2. **Domain terms in combination.** `rg -l "reset.*token|token.*reset"` — narrows to the specific intersection.
3. **Related HTTP surface.** `rg -l "POST.*reset|/auth/reset|route.*reset"` if the feature touches the API layer.
4. **Adjacent feature by analogy.** If the feature is "password reset" and the repo has "email verification", the verification files are your pattern reference. `rg -l "email.*verif"`.

**Polyglot note.** Constrain by language of the affected layer: `--type py`, `--type ts`, `--type rb`. The infra-architect agent already knows the repo's languages from `ANALYSIS.json` / `test-harness.json`. Do not grep binary files, lockfiles, or `dist/` output.

## Step 3: Identify Entry Points, Follow Imports Shallowly

From Step 2's candidates, pick **entry points** — the files a request/call/event first hits. Typical entry points:

- HTTP routes (`routes.py`, `app/controllers/`, `pages/api/`, `src/routes/`)
- CLI handlers (`cli.py`, `bin/`, `commands/`)
- Event handlers (`handlers/`, `consumers/`, `workers/`)
- Framework-specific (`page.tsx`, `+page.svelte`, Rails actions)

From each entry point, follow imports **one or two levels deep**. Stop there. Do not transitively chase every helper — the planner does not need the full graph.

**Rule of thumb:** if a file is 3 hops from the entry point, it is almost certainly not relevant to this feature.

## Step 4: Find a Pattern Reference (Sibling Feature)

Find one feature already in the repo that solves an analogous problem. This is the **pattern reference** — the planner will tell the coder to mirror it.

Examples:
- New CRUD endpoint → find an existing CRUD endpoint in the same framework
- New background job → find an existing job in the same queue system
- New React form → find an existing form component with validation

Usually 1-2 files. If nothing analogous exists, note that in CONTEXT.md under "Pattern Reference" as "none — new pattern for this repo."

## Step 5: Classify Files — Modify vs. Read-Only vs. Ignore

Bucket every candidate into one of three:

| Bucket | Meaning | Example |
|---|---|---|
| **Modify** | Feature cannot ship without changing this file | `routes.py` where the new endpoint lives |
| **Read-only** | Must be understood but not changed | `models/User.py` if you import it unchanged |
| **Ignore** | Matched your grep but unrelated | Old migration mentioning "reset" in a comment |

Explicitly drop the ignore bucket. Do **not** include files you searched and rejected — that wastes planner tokens.

## Step 6: Extract 2-4 Pattern Snippets

From the pattern-reference files, copy **short** snippets (5-15 lines each) that demonstrate the conventions the new feature must follow. Good snippets show:

- How errors are raised and caught
- How config/env is accessed
- How the return shape / response envelope looks
- How tests are structured (one test function as a template)

Do **not** copy full files. Do **not** copy more than ~60 lines total across all snippets.

## Step 7: Write CONTEXT.md

Create `${DIRIGENT_RUN_DIR}/CONTEXT.md` with exactly these sections:

```markdown
# Context for Feature: {feature name from SPEC}

## Entry Points
{The file(s) where a request/call/event for this feature first lands.
 One line per entry point with path and 1-sentence role.}

- `src/routes/auth.py:L42` — POST handler for `/auth/reset` (to be added here)

## Files to Modify
{Files that MUST change to ship the feature. Path + one-liner per file.
 If the file does not yet exist, mark as NEW.}

- `src/routes/auth.py` — add `POST /auth/reset` endpoint
- `src/services/password.py` (NEW) — token generation + hashing logic
- `tests/test_auth.py` — add reset flow tests

## Files to Read (Dependencies, do NOT modify)
{Files the coder must understand to modify the above, but will not change.
 Path + why it matters.}

- `src/models/user.py` — User model with `email` and `password_hash` columns
- `src/services/email.py` — `send_email(to, template, ctx)` helper used for delivery
- `src/config.py` — `TOKEN_TTL_MINUTES` setting

## Pattern Reference
{One analogous feature already in this repo. Planner tells coder to mirror it.
 Empty if none — say so explicitly.}

Mirror: `src/routes/auth.py` `POST /auth/verify-email` (lines 78-120) — same
token-issue → email-send → confirm-via-link shape.

## Pattern Snippets
{2-4 short snippets (5-15 lines each) showing conventions to follow.
 Error handling, config access, response shape, test shape.}

### Error raising (from src/routes/auth.py)
```python
if not user:
    raise HTTPException(status_code=404, detail="user_not_found")
```

### Response envelope (from src/routes/auth.py)
```python
return {"ok": True, "data": {...}}
```

### Test shape (from tests/test_auth.py)
```python
def test_verify_email_happy_path(client, user_factory):
    user = user_factory()
    resp = client.post("/auth/verify-email", json={"token": "..."})
    assert resp.status_code == 200
```

## Integration Points
{Where the new feature wires into existing code. Specific call sites,
 not generic statements.}

- `src/routes/auth.py` — register new route in the existing `router = APIRouter()` block at L14
- `src/services/email.py` — call `send_email(user.email, "password_reset", {token})`
- `src/models/user.py` — no schema change; reuse `password_hash` column

## Out of Scope for This Scan
{Things you looked at and deliberately did not include, with reason.
 Keeps the planner from re-discovering rejected paths.}

- Admin password-force-reset (separate feature, different route)
- OAuth flows in `src/routes/oauth.py` (not password-related)
```

### What does NOT go in CONTEXT.md

- `README.md`, top-level docs, ADRs — unless a doc contains a pattern rule the coder must follow
- `node_modules/`, `dist/`, `build/`, `.venv/`, `vendor/`, `.git/`, `__pycache__/`
- Lockfiles (`package-lock.json`, `uv.lock`, `Gemfile.lock`)
- Generated code (`*.pb.go`, `schema.graphql` generated clients, OpenAPI generated types)
- Migrations older than the current feature's history, unless the feature changes schema
- Test fixtures unless they are the pattern reference
- Full file bodies — only short snippets

## Step 8: Validate Size Budget

CONTEXT.md must be **lean**. Hard ceilings:

| Metric | Budget | Hard cap |
|---|---|---|
| Total lines | ≤ 200 | 300 |
| Total tokens | ≤ 3k | 5k |
| Files listed (Modify + Read) | ≤ 15 | 25 |
| Pattern snippets | 2-4 | 6 |

If you exceed the hard cap, the scan is not "quick" anymore and the planner will drown. Trim the Read-only bucket first, then drop borderline snippets.

Check with:
```bash
wc -l "${DIRIGENT_RUN_DIR}/CONTEXT.md"
```

**Stopping rule.** Do not spend more than 10 minutes scanning. If after 10 minutes you still cannot identify an entry point or pattern reference, write what you have and note the uncertainty in "Out of Scope for This Scan". The planner will handle the gap.

## Anti-Patterns

<anti-patterns>
| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| `rg "."` and list everything that matched | Planner drowns; no signal | Grep for feature-specific terms from Step 1 |
| Paste full file bodies | Blows the token budget, defeats the "quick" in quick-scan | 5-15 line snippets from the pattern reference only |
| Include `README.md` as a dependency | README is prose, not pattern; coder won't learn from it | Extract the concrete convention into a snippet |
| Follow imports to depth 5+ | Transitive chase pulls in the whole graph | Stop at depth 2 from entry point |
| List tests in "Files to Read" | Tests aren't dependencies; they're pattern templates | Put one test function as a snippet under "Pattern Snippets" |
| Include vendored / generated / lockfile paths | Coder never edits them; wastes planner attention | Exclusion list in Step 7 |
| Skip the sibling-feature pattern reference | Coder reinvents conventions; entropy goes up | Always find one, or explicitly say "none" |
| Write CONTEXT.md without classifying (mixed bucket) | Planner can't distinguish modify from read | Step 5 three-bucket classification, drop Ignore |
| Scan every language in a polyglot repo | 80% of the hits are irrelevant | Constrain `--type` to the feature's layer |
| Commit CONTEXT.md to the repo | It's transient planner fuel, not docs | Lives in `${DIRIGENT_RUN_DIR}`, no commit step |
</anti-patterns>

## Rules

<rules>
<rule>Scan smart, not exhaustive — if you're reading more than 15 files, you've left Hybrid territory and should have taken the Legacy route</rule>
<rule>Every entry in "Files to Modify" must have a one-sentence reason tied to the SPEC — no file listed without justification</rule>
<rule>Always name one Pattern Reference (analogous existing feature) or explicitly write "none — new pattern for this repo"</rule>
<rule>Pattern snippets are 5-15 lines each, total ≤ 60 lines across all snippets — never paste full files</rule>
<rule>Constrain grep by language (--type) based on the feature's layer — do not scan the whole polyglot tree</rule>
<rule>Follow imports at most 2 levels deep from entry points — transitive chase is out of scope</rule>
<rule>Do NOT include tests in "Files to Read" — tests belong as pattern snippets, not dependencies</rule>
<rule>Exclude node_modules, dist, build, vendor, .venv, .git, __pycache__, lockfiles, and generated code — never list them</rule>
<rule>README and top-level docs do NOT go in CONTEXT.md unless they encode a hard convention the coder must follow — extract the convention as a snippet instead</rule>
<rule>CONTEXT.md is transient — lives in ${DIRIGENT_RUN_DIR}, never committed, no start.sh, no test-harness.json produced here</rule>
<rule>If you cannot find an entry point within 10 minutes, write what you have and note the gap in "Out of Scope for This Scan" — do not stall</rule>
<rule>Match CONTEXT.md's sections to what create-plan reads (Entry Points, Files to Modify, Files to Read, Pattern Reference, Pattern Snippets, Integration Points, Out of Scope) — the planner relies on these names</rule>
</rules>

<constraints>
<constraint>Output: `${DIRIGENT_RUN_DIR}/CONTEXT.md` only — no repo files, no commit</constraint>
<constraint>Maximum 10 minutes of scanning</constraint>
<constraint>CONTEXT.md ≤ 200 lines / ≤ 3k tokens (hard cap 300 lines / 5k tokens)</constraint>
<constraint>Files listed ≤ 15 (hard cap 25) — if you need more, you're in Legacy territory, not Hybrid</constraint>
</constraints>
