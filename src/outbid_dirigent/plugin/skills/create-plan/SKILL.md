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

1. **Required:** `${DIRIGENT_RUN_DIR}/SPEC.md` — the feature specification (just written or pre-existing)
2. **Optional:** `${DIRIGENT_RUN_DIR}/BUSINESS_RULES.md` — business rules to preserve (Legacy route)
3. **Optional:** `${DIRIGENT_RUN_DIR}/CONTEXT.md` — relevant file analysis (Hybrid route)
4. **Optional:** `${DIRIGENT_RUN_DIR}/test-harness.json` — e2e test harness (base URL, auth, seed data, verification commands)
5. **Optional:** `ARCHITECTURE.md` — system architecture (if not already read in Step 0)
6. **Optional:** `CONVENTIONS.md` — project coding conventions and patterns. If present, task descriptions MUST reference relevant conventions so coder instances follow established patterns.
7. **Optional:** `.opencode/skills/` — if this directory exists, list available skills by reading their SKILL.md frontmatter (the `name` and `description` fields). For each task, set the `convention_skills` array to skill names the coder should load. Match based on task content: Ruby files → `ruby-code-writing`, forms → `form-builder`, API endpoints → `api-v1-endpoints`, React → `react-components`, tests → `selenium-tests`, etc.
8. **Optional:** `${DIRIGENT_RUN_DIR}/testing-strategy.md` — proposed test layers, frameworks, patterns (Greenfield route). Tasks must follow this strategy.
9. **Optional:** `${DIRIGENT_RUN_DIR}/architecture-decisions.md` — proposed patterns, file organization, conventions (Greenfield route). Tasks must follow these decisions.

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
      "description": "Was in dieser Phase passiert",
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
          "convention_skills": ["ruby-code-writing", "form-builder"]
        }
      ]
    }
  ],
  "estimated_complexity": "medium",
  "risks": ["Potentielle Risiken"]
}
```

## Rules

1. **Max 4 phases, max 4 tasks per phase**
2. Each task is atomic (does exactly one thing)
3. No dependencies between tasks within a phase
4. Tasks must be concrete and executable
5. If `BUSINESS_RULES.md` exists: all rules must be preserved
6. **model**: "haiku" for simple tasks, "sonnet" for standard, "opus" for complex architecture
7. **effort**: "low" for mechanical, "medium" for standard, "high" for complex logic
8. **test_level**: "L1" for unit tests/lint, "L2" for integration tests, empty if no testing needed
9. If `test-harness.json` exists: plan verification tasks that use its verification_commands and e2e_framework.run_command. The reviewer will use these to verify features end-to-end.
10. **Plan for maintainability** — the agent executing these tasks is the long-term maintainer of the codebase. Task descriptions should guide toward scalable patterns: clear interfaces, separation of concerns, explicit dependencies. Do not plan throwaway code.
11. **Plan for real verification** — each phase will be reviewed with executable verification commands. Do not plan tasks that "work" only in the sense that they compile. The reviewer will hit real endpoints and run real test suites.
12. **convention_skills**: If `.opencode/skills/` exists, tag each task with the skill names the coder should load. Be specific — a task creating a Ruby form object needs `["ruby-code-writing", "form-builder"]`, not the entire skill list. Empty array `[]` if no convention skills are relevant.

## Validation (MANDATORY)

After writing PLAN.json, validate it:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py ${DIRIGENT_RUN_DIR}/PLAN.json
```

If validation fails, fix the errors and re-run until it passes.
