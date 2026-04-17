---
name: create-plan
description: Create a phased execution plan (PLAN.json) from spec and repo context
context: fork
agent: infra-architect
---

# Create Execution Plan

## Step 0: Resolve the Spec

Check for an existing spec in this order:

1. `${DIRIGENT_RUN_DIR}/SPEC.md` — written by the Dirigent CLI pipeline
2. `SPEC.md` in repo root
3. `.planning/SPEC.md`

**If a spec file exists:** read it and skip to Step 1.

**If no spec file exists:** generate one from user input.

### Generating a Spec

Check `$ARGUMENTS` for a feature description and for `--yolo`.

**Gather context first** — read these well-known files if they exist (regardless of mode):

- `ARCHITECTURE.md` — understand the system structure
- `README.md` — understand what the project does
- `package.json` or `pyproject.toml` — understand the tech stack
- `${DIRIGENT_RUN_DIR}/test-harness.json` — understand test infrastructure

**Normal mode** (no `--yolo`):

Using the feature description from `$ARGUMENTS` and the context you gathered, ask the user **at most 2-3 targeted questions** to fill in gaps. Focus only on things you genuinely cannot infer from the codebase:

- Scope boundaries (what's in vs out)
- Integration points that are ambiguous
- User-facing behavior that has multiple valid interpretations

Do NOT ask about:
- Tech stack (you can see it)
- File structure (you can see it)
- Testing approach (you can see it)
- Anything you can answer by reading the code

If the description is already clear and the codebase gives you enough context, ask zero questions.

**Yolo mode** (`--yolo` in arguments):

Ask zero questions. Use the feature description and codebase context to make reasonable assumptions. Document every assumption in the spec's `## Assumptions` section.

### Write the Spec

Write `${DIRIGENT_RUN_DIR}/SPEC.md`:

```markdown
# {Feature Title}

## Goal
{One paragraph: what this feature does and why}

## Requirements
{Bulleted list of concrete, testable requirements}

## Assumptions
{Bulleted list — especially important in --yolo mode}

## Out of Scope
{What this does NOT include}
```

Keep it short — 20-40 lines max. The spec exists to give the planner enough context, not to be a PRD.

---

## Step 1: Read Context

Read all available context files:

0. **Required if present:** `${DIRIGENT_RUN_DIR}/SPEC.compact.json` — pre-compacted requirements with stable IDs (R1, R2, …), glossary, entities, and flows. When this exists, you MUST tag every task in the plan with its `relevant_req_ids` (see Step 3 and Rule 13).
1. **Required:** `${DIRIGENT_RUN_DIR}/SPEC.md` — the feature specification (just written or pre-existing)
2. **Optional:** `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` — business rules to preserve (Legacy route)
3. **Optional:** `${DIRIGENT_RUN_DIR}/CONTEXT.md` — relevant file analysis (Hybrid route)
4. **Optional:** `${DIRIGENT_RUN_DIR}/test-harness.json` — e2e test harness (base URL, auth, seed data, verification commands)
5. **Optional:** `ARCHITECTURE.md` — system architecture with XML-tagged sections. Key sections for planning:
   - `<testing-verification>` — build/test/e2e commands, test strategy. Tasks must follow this.
   - `<architecture-decisions>` — patterns, file organization, scaffold decisions. Tasks must follow these.
   - `<key-patterns>` — coding conventions and patterns. Task descriptions MUST reference relevant patterns.
6. **Optional:** `.opencode/skills/` — if this directory exists, list available skills by reading their SKILL.md frontmatter (the `name` and `description` fields). For each task, set the `convention_skills` array to skill names the coder should load. Match based on task content: Ruby files → `ruby-code-writing`, forms → `form-builder`, API endpoints → `api-v1-endpoints`, React → `react-components`, tests → `selenium-tests`, etc.
10. **Optional:** `.brv/context-tree/` — if this directory exists and `brv` CLI is available, run `brv query "What are the key domain patterns, rules, and architectural decisions for this project?"` to gather domain knowledge. Incorporate relevant findings into task descriptions so coder instances have domain context.

## Step 2: Analyze the Repo

Explore the repository structure relevant to the feature. Understand:
- Project language and framework
- Existing patterns and conventions
- File organization
- Available test infrastructure

## Step 3: Create the Plan

Write `${DIRIGENT_RUN_DIR}/PLAN.json` with this exact format:

```json
{
  "title": "Feature-Titel",
  "summary": "Kurze Beschreibung was implementiert wird",
  "assumptions": ["Annahmen ueber die Codebase"],
  "out_of_scope": ["Was NICHT gemacht wird"],
  "phases": [
    {
      "id": "01",
      "name": "Phase-Name",
      "kind": "user-facing",
      "description": "Was in dieser Phase passiert",
      "merge_justification": "Ein Satz: warum diese Phase nicht mit der naechsten gemerged werden kann. Leer nur bei der letzten Phase.",
      "tasks": [
        {
          "id": "01-01",
          "name": "Task-Name",
          "description": "Detaillierte Beschreibung was zu tun ist",
          "files_to_create": ["neue/dateien.ext"],
          "files_to_modify": ["existierende/dateien.ext"],
          "depends_on": [],
          "model": "sonnet",
          "effort": "medium",
          "test_level": "L1",
          "convention_skills": ["ruby-code-writing", "form-builder"],
          "relevant_req_ids": ["R3", "R7"]
        }
      ]
    }
  ],
  "estimated_complexity": "medium",
  "risks": ["Potentielle Risiken"]
}
```

## Phase kind — how each phase relates to the user

Every phase declares a `kind` at plan time. Pick one:

| kind | when to pick | examples |
|---|---|---|
| `user-facing` | Phase delivers something a user clicks, types, or sees | "Admin user management UI", "Checkout flow", "Dark mode toggle" |
| `integration` | Phase delivers a subsystem another phase will expose to users | "Auth middleware + session", "tRPC router scaffold", "Background job runner" |
| `infrastructure` | Scaffolding, migrations, tooling, CI. No consumer within the run | "Scaffold Next.js + Prisma", "Set up CI" |

Downstream the contract validator enforces layer quotas based on this kind.
Pick wrong and the contract step will loudly reject the contract.

**Constraints enforced by the validator:**
- Max 1 `infrastructure` phase per plan. If you're thinking of two, merge them.
- Final phase must NOT be `infrastructure` — every run has to end on
  user-observable delivery.
- Two consecutive same-kind phases are a merge warning. If you keep them
  separate, the `merge_justification` must make a strong case.

## The merge-justification rule

Every phase except the last must have a `merge_justification` — one sentence
on why this phase cannot be merged with the next. The sentence is the forcing
function: if you can't write it, merge the phases.

Good justifications:
- "Exposes the auth API that phase 3's login UI consumes — splitting lets the
  auth contract probe the backend in isolation before UI lands on top."
- "Scaffolding Next.js and Prisma together produces a non-runnable
  intermediate state if split — kept as one infrastructure phase."
- "Delivers the admin user-management UI end-to-end; next phase introduces
  reporting which depends on this screen being stable."

Bad justifications (= merge these):
- "Separate concern." (vague)
- "Cleaner organization." (vague)
- "Makes each phase smaller." (self-fulfilling; re-merge them)

## When to use `size: "large"`

Default is `"standard"` — 4 phases × 4 tasks. This cap is the forcing function
that keeps plans atomic and reviewable. Set `"size": "large"` (raises caps to
5 phases × 5 tasks) only when the spec genuinely doesn't fit 4×4 and the only
alternative is a phase densely packed with multiple `effort: "high"` tasks.

Appropriate for `"large"`:
- Features with ≥3 distinct screens AND non-trivial logic per screen.
- Subsystems requiring multiple integration phases with distinct downstream contracts.
- Migrations that cannot be atomically split without leaving intermediate broken states.

If you set `"large"`, the `summary` must explain why in one sentence so reviewers
can evaluate the expansion. Don't use `large` to avoid thinking; use it when a
4×4 plan would compress genuinely separate work into dense phases.

Max 1 infrastructure phase and "final phase ≠ infrastructure" apply regardless
of size.

## Rules

1. **Max 4 phases × 4 tasks per phase** (default). Pydantic and the validator both reject violations. Set `"size": "large"` to raise caps to 5×5 when genuinely needed — otherwise split the SPEC into multiple dirigent runs.
2. **Every phase has a `kind`** — `user-facing`, `integration`, or `infrastructure`. Required. See the table above.
3. **Every phase except the last has a `merge_justification`** — one sentence, see the rule above.
4. **Max 1 infrastructure phase.** Scaffolds, migrations, and CI setup almost always belong together.
5. **Final phase MUST be `user-facing` or `integration`, not `infrastructure`.** A run that ends on infra delivered nothing observable.
6. Each task is atomic (does exactly one thing).
7. No dependencies between tasks within a phase.
8. Tasks must be concrete and executable.
9. If `BUSINESS_RULES.md` exists: all rules must be preserved.
10. **model**: "haiku" for simple tasks, "sonnet" for standard, "opus" for complex architecture.
11. **effort**: "low" for mechanical, "medium" for standard, "high" for complex logic.
12. **test_level**: "L1" for unit tests/lint, "L2" for integration tests, empty if no testing needed.
13. If `test-harness.json` exists: plan verification tasks that use its verification_commands and e2e_framework.run_command.
14. **Plan for maintainability** — task descriptions should guide toward scalable patterns: clear interfaces, separation of concerns, explicit dependencies.
15. **Plan for real verification** — each phase will be reviewed with executable commands. The reviewer will hit real endpoints and run real test suites.
16. **convention_skills**: If `.opencode/skills/` exists, tag each task with the skill names the coder should load. Empty array `[]` if no convention skills are relevant.
17. **relevant_req_ids (spec coverage)**: If `${DIRIGENT_RUN_DIR}/SPEC.compact.json` exists, set `relevant_req_ids` on every task. Together, all tasks must collectively reference every requirement at least once. Cross-cutting requirements (encryption, audit logging, GDPR) may be referenced by multiple tasks.

## Validation (MANDATORY)

After writing PLAN.json, validate it:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py ${DIRIGENT_RUN_DIR}/PLAN.json
```

If validation fails, fix the errors and re-run until it passes.
