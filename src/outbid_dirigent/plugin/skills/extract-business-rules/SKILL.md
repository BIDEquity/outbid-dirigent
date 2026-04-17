---
name: extract-business-rules
description: Extract business rules from an existing codebase into BUSINESS_RULES.md so the planner and executor preserve them during a rewrite or migration.
context: fork
agent: infra-architect
---

# Extract Business Rules

You read an established codebase and write `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` — a compact, source-linked inventory of the rules the Legacy route must preserve. This file is consumed downstream by:

- `spec-compactor` (may merge rules into `SPEC.compact.json` if business rules are available)
- `create-plan` — planner tags tasks against the rules (`relevant_req_ids`)
- `implement-task` — executor treats the rules as non-negotiable invariants
- `review-phase` — reviewer checks that no rule was silently broken

Get this wrong and the rewrite silently changes behavior the business depends on. Get it right and the downstream steps cannot violate domain logic without noticing.

## Realism — Read This First

Legacy codebases are big. You will NOT read every file. You will NOT find every rule. The goal is a **durable, honest inventory** of the rules that actually govern behavior — with source citations — plus explicit notes about what you deliberately skipped.

- Target: the top ~50 files by business-logic density (see Step 2 for how to pick).
- Budget: roughly 20–30 minutes of reading. If you are past that, write what you have and flag the rest with `[UNCLEAR]` or `[NOT REVIEWED]`.
- Honesty beats completeness. A short list with citations beats a long list of guesses.

## Steps At A Glance

| # | Step | Output |
|---|---|---|
| 1 | Check for prior Proteus extraction | Decide: transcribe or extract fresh |
| 2 | Scope the codebase — pick which ~50 files to read deeply | File shortlist in memory |
| 3 | Extract rules using the heuristics (Step 4) | Draft rules with file:line citations |
| 4 | Categorize into the seven sections | Structured draft |
| 5 | Flag uncertainty and what you skipped | `[UNCLEAR]` / `[NOT REVIEWED]` annotations |
| 6 | Write `BUSINESS_RULES.md` | `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` |
| 7 | Validate against the quality checklist | Pass/fail |
| 8 | Commit (optional — file lives in `.dirigent/`) | Commit only if user asked |

## When This Runs

Legacy route, after Init. You have:

- `${DIRIGENT_RUN_DIR}/SPEC.md` — what the user wants built (new / replacement / migration)
- The live repo — you read from it; you do NOT modify it
- Possibly `.proteus/rules.json` (and siblings) if Proteus ran earlier — see Step 1

Output: `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` (markdown, human- and LLM-readable).

## Step 1: Check for Prior Proteus Extraction

Before you read a single source file, check whether Proteus already ran:

```bash
ls .proteus/rules.json .proteus/fields.json .proteus/events.json 2>/dev/null
```

**Decision rule:**

| Situation | What to do |
|---|---|
| `.proteus/rules.json` exists and is non-empty | Transcribe it — do NOT re-extract from scratch. Read the JSON, convert each rule into the per-rule template (Step 4), keep the Proteus source refs. Spot-check 3–5 rules against the live code to confirm they still hold. Add new rules only for gaps you find in spot-checks. |
| `.proteus/` missing or empty | Extract fresh using Steps 2–5. |
| `.proteus/rules.json` exists but looks stale (git log shows heavy churn since) | Transcribe as a starting point, then re-verify hot paths. Annotate stale rules `[VERIFY]`. |

Proteus extraction is invoked separately by the Legacy route's executor — if it ran, its output is authoritative. Do not duplicate work.

## Step 2: Scope — Pick Which Files to Read

You cannot read everything. Prioritize in this order and stop when you hit the ~50-file budget:

**Read deeply (tier A):**
1. **Entry points** — routes, controllers, CLI commands, message/queue handlers, cron entries. These reveal what the system actually does.
2. **Domain models / schemas** — ORM models, Pydantic/Zod schemas, DB migrations (the *latest* state — not historical migrations). Reveals entities + field constraints.
3. **Validators / guards** — files named `validators`, `validation`, `rules`, `policies`, `permissions`, `guards`. Rules live here by definition.
4. **Service / domain layer** — files under `services/`, `domain/`, `usecases/`, `workflows/`. Branching logic here is business logic.

**Sample (tier B — read 1–2 representative files per category):**
5. Utility / helper modules — skim for shared validation helpers, then return.
6. Background jobs / workers — usually thin wrappers over services.

**Skip entirely (tier C):**
- Tests (useful as *evidence* for a rule, but don't extract rules *from* them)
- Frontend styling (CSS / Tailwind / styled-components)
- Historical DB migrations (only the current schema matters)
- Vendored deps / `node_modules` / `.venv`
- Generated code (protobufs, OpenAPI clients, etc.)
- Build configs, CI YAML, Dockerfiles
- i18n translation files / UI copy
- Logging boilerplate

If the repo is polyglot, cover the backend / domain language first. Frontend-only rules (e.g. form UX) are secondary unless the SPEC is a UI rewrite.

**If you run out of budget:** stop. List what you skipped under `## Not Reviewed` in the output.

## Step 3: Extraction Heuristics — Where Rules Hide

When reading a file, look specifically for these patterns. Most rules live in a handful of syntactic shapes:

| Signal | What it usually means | Examples |
|---|---|---|
| `if <condition>: raise <DomainError>` | Business invariant | `if order.total < 0: raise InvalidOrder` |
| `assert <condition>, "<message>"` | Invariant (weaker — confirm it's not just a dev check) | |
| Guard clauses at function start (`if not X: return None/False`) | Precondition | |
| Schema constraints (`min_length`, `max`, `regex`, `gt=`, `ge=`) | Field-level rule | Pydantic, Zod, marshmallow, DB CHECK |
| Decorators: `@requires_*`, `@permission_*`, `@validates` | Policy / authorization | |
| `status in [...]` / `state == "..."` checks before actions | State-machine transitions | |
| Numeric literals used in comparisons (`> 100`, `<= 30`) | Threshold / limit | Track the magic number — document exact value |
| `try/except <SpecificDomainError>` | Known failure mode + recovery | |
| Calculation functions (`calculate_*`, `compute_*`, `_total`, `_fee`) | Business formulas | Record the formula exactly |
| DB unique / not-null / CHECK / foreign-key constraints | Data invariants | Read the current schema, not old migrations |
| Event emission (`emit(...)`, `publish(...)`, `dispatch(...)`) | Domain event — goes in "Domain Events" section | |
| External API calls in service layer | Dependency — goes in "External Dependencies" | |

**Grep-like patterns to start with** (adapt to the repo's language):

```
# Python
grep -rn "raise.*Error\|raise.*Exception" --include="*.py" <domain_dir>
grep -rn "^\s*if\s" --include="*.py" <domain_dir> | head -200
grep -rn "@validator\|@validates\|@field_validator" --include="*.py"

# JS/TS
grep -rn "throw new" --include="*.ts" <domain_dir>
grep -rn "z\.\|yup\.\|joi\." --include="*.ts"

# Any
grep -rn "TODO\|FIXME\|HACK\|XXX\|BUG" <domain_dir>  # flags explicit known quirks
```

Use these as *starting points*, not substitutes for reading the surrounding context.

## Step 4: Rule Template — One Rule, One Block

Every rule in the output uses this shape. This keeps rules machine-readable and source-linked:

```markdown
### BR-{NN}: {short imperative name}
- **Statement:** {one sentence, present tense, what must hold}
- **Trigger:** {when this rule is evaluated — e.g. "on order submission", "on user signup"}
- **Effect:** {what happens if violated — e.g. "request rejected with 400", "order.status = 'on_hold'"}
- **Source:** `{path/to/file.py}:{line}` ({function_name})
- **Evidence:** `{exact code snippet, 1–3 lines, quoted}`
- **Confidence:** HIGH | MEDIUM | LOW — {1-phrase justification}
- **Notes:** {optional — e.g. "[UNCLEAR] whether this also applies to B2B orders"}
```

**Numbering:** `BR-01`, `BR-02`, … stable, sequential, never reused.

**Statement form:** imperative and testable. Bad: *"orders are validated"*. Good: *"An order MUST have at least one line item before it can be submitted."*

**Source citation is mandatory.** No citation = don't include the rule; drop it or mark it `[UNCLEAR]`.

## Step 5: Categorize Into Sections

Group the `BR-NN` entries under the seven section headers below. Entities, API endpoints, schema, and external deps are *context* for the rules — they are not themselves rules, but the planner needs them.

Skeleton:

````markdown
# Business Rules — {PROJECT_NAME}

_Extracted from commit `{git_rev_parse_HEAD}` on {date}. Source-of-truth: the code at that commit._

## Scope

- **Reviewed:** {list of top-level dirs / modules you read deeply, ~1–2 lines}
- **Sampled:** {dirs you only skimmed}
- **Not Reviewed:** {dirs you deliberately skipped, with 1-phrase why}

## Core Entities

Each entity = a domain object with business meaning (not every DB table).

### {EntityName}
- **Fields:** `field: type` — constraint if any (e.g. `email: str — unique, lowercased`)
- **Source:** `{path}:{line}`
- **Notes:** {lifecycle states if applicable}

## Business Rules

{BR-01, BR-02, … using the Step 4 template. Group by entity or flow if the list is long (>20 rules).}

## Domain Events

What happens when, causally. One line per event.

- **{EventName}** — emitted at `{path}:{line}` when `{trigger}` → subscribers: {list or "none"}

## API Endpoints

Only the endpoints that exist, with their guards. Not a full OpenAPI spec.

| Method | Path | Auth | Input (shape) | Success | Error codes |
|---|---|---|---|---|---|
| POST | /orders | required | OrderCreate | 201 Order | 400, 401, 422 |

## Database

Current schema state. Constraints only, not every column.

- **{table}** — PK `{col}`, UNIQUE `({cols})`, FK `{col} -> {table}.{col}`, CHECK `{expr}`
- Source: `{migration/model file}:{line}`

## External Dependencies

| Service | Called from | Purpose | Failure mode |
|---|---|---|---|
| Stripe API | `payments/charge.py` | card charging | retries 3x, then Order.status='payment_failed' |

## Edge Cases & Known Quirks

Special-cases you found. Often TODO/FIXME comments or odd branches.

- **{Case}** — `{path}:{line}` — {what it does, why it's odd}

## Open Questions

Things you couldn't determine from the code. The planner will surface these to the user.

- [UNCLEAR] {question}

## Not Reviewed

Directories / modules you deliberately skipped and why. The next run may revisit these.

- `web/static/` — CSS only, no domain logic
- `migrations/2019_*` — historical migrations, current schema captured via models
````

## Step 6: Write the File

Write `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` exactly. Downstream code reads this path — do not change it.

```bash
# Verify the directory exists (the harness creates it, but confirm)
test -d "${DIRIGENT_RUN_DIR}" || { echo "DIRIGENT_RUN_DIR missing"; exit 1; }
```

## Step 7: Validate

Before you stop, check:

1. **Every BR-NN has a `Source:` citation** with a real `path:line`.
2. **Every BR-NN has `Confidence:` marked.** If you are unsure, mark LOW — don't hide uncertainty.
3. **No rule is a restatement of a framework idiom.** (See Anti-Patterns below.)
4. **`## Scope` section lists what you did NOT read.** Empty Scope section = you probably missed things.
5. **At least one BR per major entry point.** If `/orders` is a route and you have zero rules about orders, you didn't read deeply enough.
6. **File is under ~800 lines.** If it's longer, you're extracting too much trivia — prune.

## Step 8: Commit (optional)

`BUSINESS_RULES.md` lives in `${DIRIGENT_RUN_DIR}` (usually `.dirigent/`) which may be gitignored. Only commit if the user explicitly asked, or if the project convention is to track `.dirigent/` artifacts.

```bash
# Only if .dirigent/ is tracked:
git add .dirigent/BUSINESS_RULES.md
git commit -m "docs: extract business rules from legacy code"
```

## Anti-Patterns — Do NOT Extract These

These are NOT business rules. Do not put them in the file. Including them dilutes the signal for the planner and executor.

| Not a rule | Why |
|---|---|
| Type checks (`isinstance(x, str)`) | Language-level idiom, not domain constraint |
| Null guards (`if x is None: return`) | Defensive coding, not business logic |
| Framework config (allowed hosts, CORS origins, middleware order) | Infra, not domain |
| Logging / telemetry calls | Observability, not rules |
| CSS / layout rules ("prices right-aligned") | UI polish, not business |
| i18n / translation strings | Localization, not rules |
| Test assertions | Tests *verify* rules; they don't *define* them — cite the implementation, not the test |
| Historical migrations | Current schema is canonical |
| Retry/backoff config | Infra behavior, not domain (unless retry *count* has a business meaning like "3 payment attempts before lockout") |
| Import ordering, linter settings | Tooling, not rules |
| Auth-library defaults ("passwords must be 8+ chars" from the library) | Only extract if the code *overrides* or *adds to* the default |

**Borderline cases — use judgment:**
- Rate limits: extract if the *limit value* matters to the business ("max 100 orders/min per user"). Skip if it's generic DOS protection.
- Feature flags: extract only the *rule being gated*, not the flag check itself.

## Rules

<rules>
<rule>Every rule MUST have a `path:line` source citation. Rationale: the planner and executor need to verify rules against code; uncited rules are guesses and get silently violated.</rule>
<rule>Prefer transcribing prior Proteus output over re-extracting. Rationale: Proteus does deeper static analysis than an LLM read-through; duplicate work risks contradicting it.</rule>
<rule>Cap reading at ~50 files / ~30 minutes. List what you skipped. Rationale: completeness is impossible on legacy codebases; honest scoping beats fake completeness.</rule>
<rule>Use the BR-NN template for every rule. Rationale: downstream skills parse this shape; ad-hoc prose rules get ignored.</rule>
<rule>Mark uncertainty with `[UNCLEAR]` and `Confidence: LOW`. Rationale: the user can answer open questions; hidden guesses cannot be reviewed.</rule>
<rule>Do NOT extract anti-pattern items (framework idioms, null guards, CSS, i18n, infra config). Rationale: noise in BUSINESS_RULES.md forces the executor to reason about non-rules, degrading task quality.</rule>
<rule>Do NOT modify repo source files. This skill is read-only on the repo. Rationale: extraction must be reversible and non-destructive; the Legacy route has later phases for code changes.</rule>
<rule>Output path is `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` exactly — do not rename. Rationale: `oracle.py`, `task_runner.py`, `create-plan`, and `implement-task` all hard-code this path.</rule>
<rule>Keep the output under ~800 lines. Rationale: it is concatenated into every executor prompt; oversize files blow the context budget.</rule>
<rule>Do NOT invent rules from tests. Cite the implementation the test exercises, not the test itself. Rationale: tests can lag behind code; the implementation is the source of truth.</rule>
</rules>

<constraints>
<constraint>Output: `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` (markdown, single file).</constraint>
<constraint>Budget: 20–30 minutes of reading, ~50 files deep-read max.</constraint>
<constraint>Read-only on the target repo — no edits to source files.</constraint>
<constraint>Do NOT create support files, tiered schemas, or new abstractions. This skill is one markdown file in, one markdown file out.</constraint>
</constraints>
