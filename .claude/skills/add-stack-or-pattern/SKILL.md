---
name: add-stack-or-pattern
description: Repo-internal maintainer skill. Add or modify a stack, interaction shape, compute topology, domain pattern, or evolution threshold in the greenfield-scaffold plugin skill, keeping ALL cross-references consistent.
---

## Architecture is Three Axes

Remember: the greenfield skill uses THREE architectural axes, not one:
- **Interaction Shape** (5 options): Sync REST / Streaming / Event-Driven / Real-time / Batch — each has its own file under `architecture-patterns/`
- **Compute Topology** (3 options): In-Process / Serverless / Long-running Worker — described in `architecture-patterns/README.md` (no separate files)
- **Domain Patterns** (optional): Pipeline, Agent Loop, State Machine, Webhook Receiver, Multi-Tenant — files under `architecture-patterns/` (pipeline.md, agent-loop.md)

When adding/modifying, be precise about WHICH axis you're touching.

# Add or Modify a Stack / Architecture Pattern

**Scope:** repo-internal maintainer tool. This skill is NOT shipped with the plugin. It's for dirigent developers who need to add a new stack (e.g. Elixir + Phoenix) or a new architecture pattern (e.g. Actor Model), or modify an existing entry.

The problem this solves: stack and pattern metadata is spread across many files. Adding a new stack touches at least 5 files, and missing one silently breaks the system (agent reads stale tier table, finds broken matrix cell, etc.).

## Target Directory

All edits happen under:

```
src/outbid_dirigent/plugin/skills/greenfield-scaffold/
├── SKILL.md
└── stacks/
    ├── README.md
    ├── <stack-files>.md           # streamlit.md, fastapi.md, ...
    └── architecture-patterns/
        ├── README.md
        └── <pattern-files>.md     # sync-rest.md, streaming.md, ...
```

## What The Skill Does

1. Asks what kind of change (add stack / modify stack / add pattern / modify pattern)
2. Asks for the name and key details
3. Makes all the necessary edits across ALL referenced files
4. Runs the test suite to verify nothing broke
5. Reports a changelog of every file touched

## Decision Tree

Ask the user:

1. **What are you changing?**
   - Add a new **stack** (e.g. Phoenix, Django, SvelteKit)
   - Modify an existing **stack** (update commands, tier, pairing)
   - Add a new **architecture pattern** (e.g. Actor Model, CQRS)
   - Modify an existing **pattern** (update code examples, compatibility)
   - Deprecate / remove a stack or pattern

Then follow the matching workflow below.

---

## Workflow: Add a New Stack

### Inputs Needed

Ask the user for these fields:

| Field | Example |
|---|---|
| Stack name (kebab-case for filename) | `phoenix` |
| Display name | `Phoenix (Elixir)` |
| Role | Full-stack backend, or Python UI, or JS Frontend, ... |
| Tier | 1 (default for role) or 2 (fallback) |
| Check-installation command | `mix --version` |
| Scaffold command | `mix phx.new . --no-install` |
| Run command + port | `mix phx.server` on `4000` |
| Test command | `mix test` |
| Pattern compatibility row | 7 cells: ✓/△/✗ for each of the 7 patterns |
| Pairing suggestions | what it combines well with |
| Opinionated defaults to add | any language-specific rules (e.g. "use Ecto, not Ecto-Schema") |

### Files to Edit

**1. Create `stacks/<name>.md`**

Use this template — copy the exact section structure used in existing stack files:

```markdown
# <Display Name>

**Role:** <role>
**Tier:** <tier> (default / fallback)
**When:** <SPEC signals that indicate this stack>

## Docs

Before using unfamiliar <Display Name> APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="<library name>"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

\`\`\`bash
<check-command>
\`\`\`

## Scaffold

\`\`\`bash
<scaffold-command>
\`\`\`

## Run

\`\`\`bash
<run-command>
\`\`\`

Port: **<port>**

## Test

\`\`\`bash
<test-command>
\`\`\`

## Start Script Pattern

\`\`\`bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
<install step>
exec <run-command with 0.0.0.0 binding>
\`\`\`

## Pairing

- **+ <OtherStack1>** → <combination description>
- **+ <OtherStack2>** → ...
```

**2. Update `stacks/README.md`:**

- **Tier Table**: add the new stack to the correct row
- **Opinionated Defaults**: if this stack brings language-specific conventions (e.g. a new language), add a new subsection or rows
- **Archetype Combos** tables: if this stack enables new archetypes, add those rows (with Typical Pattern column filled in)

**3. Update `stacks/architecture-patterns/README.md`:**

- **Pattern × Stack Compatibility Matrix**: add a new row with the 7 ✓/△/✗ cells

**4. Update `SKILL.md`:**

- **Step 1A table** ("Use-Case-Archetype → Stack"): if this stack enables new archetypes, add rows
- **File Routing table**: no change needed (it uses generic `<stack-name>.md`)

### Verification

```bash
# Tests still pass
uv run pytest tests/test_greenfield_smoke.py tests/test_router.py -q

# No broken references
grep -r "<old-stack-name>\|<typo-name>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/
```

### Deliverable

Report to the user:
- Files created: N
- Files modified: N
- Tests: pass/fail
- Next step: commit with `git add -A && git commit -m "feat(greenfield): add <stack> stack"`

---

## Workflow: Modify an Existing Stack

### Identify The Stack

Find the stack file: `stacks/<name>.md`. Read it first before editing.

### Possible Changes

**A) Update commands** (scaffold/run/test):
- Edit the relevant section in `stacks/<name>.md`
- Verify the new commands work (run them in a tmp dir)
- No other files affected

**B) Change tier**:
- Edit `stacks/README.md` Tier Table
- Edit the stack file's "Tier:" line

**C) Change pattern compatibility**:
- Edit `stacks/architecture-patterns/README.md` matrix row
- Consider: does this change affect Archetype-Combos "Typical Pattern"? If yes, update `stacks/README.md` archetype tables AND `SKILL.md` Step 1A table

**D) Rename**:
- Rename the file
- Find/replace all references (6 places typically): `stacks/README.md`, `SKILL.md`, `stacks/architecture-patterns/README.md`, pairing mentions in other stack files
- **Critical**: use `grep -r "<oldname>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/` to find ALL references before renaming

### Verification

Same as Add — run tests, grep for broken references.

---

## Workflow: Add a New Architecture Pattern

### Inputs Needed

| Field | Example |
|---|---|
| Pattern name (kebab-case filename) | `actor-model` |
| Display name | `Actor Model` |
| Core idea (one sentence) | "Stateful actors react to messages, one at a time" |
| Domain signals | "state machines", "per-entity consistency", "actors" |
| Stack compatibility (11 cells) | one ✓/△/✗ per stack in the matrix |
| Code example (Python) | working skeleton |
| Libraries by stack | which library handles this pattern in each stack |
| Anti-patterns | 3-5 bullets |

**Reality check:** before adding a new pattern, ask: is this really "by the book"? The existing 7 patterns were chosen because Claude knows them from training corpus. Adding esoteric patterns (CQRS, Event Sourcing, Actor Model) may not produce cleaner code. If in doubt, DON'T add it.

### Files to Edit

**1. Create `stacks/architecture-patterns/<name>.md`**

Template (match the style of existing pattern files like `streaming.md`):

```markdown
# <Display Name>

<one-sentence description>

## When to Use

<problem characteristics that warrant this pattern>

## Core Flow

\`\`\`
<ASCII data-flow diagram>
\`\`\`

## Domain Signals

- "<signal 1>"
- "<signal 2>"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for concreteness. The pattern applies equally to TypeScript, Go, etc. Check your stack's entry in the matrix for language-specific library names.

\`\`\`python
# <working Python skeleton>
\`\`\`

## Libraries by Stack

| Stack | Idiom |
|---|---|
| <stack> | <how this pattern is implemented there> |

## Anti-Patterns

- **Don't <X>** — <reason>
- **Don't <Y>** — <reason>
```

**2. Update `stacks/architecture-patterns/README.md`:**

- **Pattern × Stack Matrix**: add a new COLUMN (one cell per stack, including a link in the header to the new pattern file)
- **The 7 Patterns table**: add a row (rename from "7" to "8" throughout the docs if this is the 8th pattern — but prefer to keep the count stable)
- **Decision Signals table**: add a row
- **Pattern Interaction section**: mention any common combos with existing patterns

**3. Update `stacks/README.md`:**

- **"Choosing Stack × Pattern"** block: no change if the list of patterns is still described generically
- **Archetype Combos** tables: if any existing archetype should now use this pattern as its default, update the Typical Pattern column

**4. Update `SKILL.md`:**

- **Step 1B** ("Architecture Pattern → Control Flow"): add a bullet for the new pattern in the list
- **Step 1A** table: update "Typical Pattern" column where relevant

### Verification

```bash
# Tests still pass
uv run pytest tests/test_greenfield_smoke.py -q

# Matrix is still complete (all cells filled)
# Manual check: open architecture-patterns/README.md and scan for empty cells
```

### Deliverable

Changelog report + commit suggestion.

---

## Workflow: Modify an Existing Pattern

### Possible Changes

**A) Update code example**:
- Edit the Python skeleton in `stacks/architecture-patterns/<name>.md`
- No other files affected

**B) Change compatibility**:
- Edit the matrix row in `stacks/architecture-patterns/README.md`
- If this flips ✗ to ✓ or vice versa for a stack, update any archetype combos that relied on the old compatibility

**C) Rename**:
- Rename file
- Find all references: `grep -r "<oldname>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/`
- Update every occurrence

### Verification + Deliverable

Same as others.

---

## Workflow: Deprecate / Remove

Removal is rarely the right answer — prefer to mark as "Tier 3" or add a warning note. If removal is truly needed:

1. Check usage: `grep -r "<name>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/`
2. Remove the file
3. Remove all references (tier table, matrix, archetype tables, SKILL.md tables)
4. Add a note to the commit message explaining why
5. Consider backwards compatibility: if the name appeared in any generated ARCHITECTURE.md files in example repos, those become stale

---

## Cross-Reference Checklist

After ANY change, grep to verify consistency. These are the files that cross-reference stacks/patterns:

```bash
# All references to a stack name
grep -rn "<stack-name>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/

# All references to a pattern name
grep -rn "<pattern-name>" src/outbid_dirigent/plugin/skills/greenfield-scaffold/
```

The expected reference locations:

| Reference | Where |
|---|---|
| Stack definition | `stacks/<name>.md` |
| Stack in tier table | `stacks/README.md` |
| Stack in matrix | `stacks/architecture-patterns/README.md` |
| Stack in archetype combos | `stacks/README.md` (3 tables: Web/AI/Mobile) |
| Stack in Step 1A table | `SKILL.md` |
| Pattern definition | `stacks/architecture-patterns/<name>.md` |
| Pattern in 7-patterns table | `stacks/architecture-patterns/README.md` |
| Pattern in matrix columns | `stacks/architecture-patterns/README.md` |
| Pattern in decision signals | `stacks/architecture-patterns/README.md` |
| Pattern in archetype combos | `stacks/README.md` + `SKILL.md` ("Typical Pattern" columns) |
| Pattern in Step 1B list | `SKILL.md` |

A complete change touches all relevant rows.

## Test After Every Change

```bash
uv run pytest tests/test_greenfield_smoke.py tests/test_router.py -q
```

If tests fail, the most likely cause is a broken reference — grep for the name you changed and look for missed spots.

## Commit Convention

- Add stack: `feat(greenfield): add <name> stack`
- Modify stack: `fix(greenfield): update <name> <what changed>`
- Add pattern: `feat(greenfield): add <name> architecture pattern`
- Modify pattern: `fix(greenfield): update <name> pattern <what changed>`
- Remove: `chore(greenfield): remove <name> (reason: ...)`

## Rules

<rules>
<rule>This skill is repo-internal — never put it under src/outbid_dirigent/plugin/</rule>
<rule>Every change touches multiple files. Use the Cross-Reference Checklist — don't rely on memory.</rule>
<rule>Before editing, grep for ALL references to the name being changed.</rule>
<rule>After editing, grep again to confirm nothing was missed.</rule>
<rule>Run the test suite after every change. Broken tests usually mean broken references.</rule>
<rule>Prefer tier changes or notes over deletion — downstream code may have generated ARCHITECTURE.md files referencing old names.</rule>
<rule>When adding a pattern, honest-check: does Claude know it well from training corpus? If no, don't add it.</rule>
<rule>Every stack file must follow the exact same section structure (Docs / Check Installation / Scaffold / Run / Test / Start Script / Pairing). Consistency matters for the agent reading these.</rule>
<rule>Every pattern file must follow the exact same section structure (When to Use / Core Flow / Domain Signals / Code Example / Libraries by Stack / Anti-Patterns).</rule>
</rules>
