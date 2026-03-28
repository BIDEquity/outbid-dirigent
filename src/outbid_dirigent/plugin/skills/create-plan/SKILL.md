---
name: create-plan
description: Create a phased execution plan (PLAN.json) from spec and repo context
---

# Create Execution Plan

## Step 1: Read Context

Read all available context files:

1. **Required:** `.dirigent/SPEC.md` — the feature specification
2. **Optional:** `.dirigent/BUSINESS_RULES.md` — business rules to preserve (Legacy route)
3. **Optional:** `.dirigent/CONTEXT.md` — relevant file analysis (Hybrid route)
4. **Optional:** `.dirigent/INIT_REPORT.md` — dev environment bootstrap results
5. **Optional:** `.dirigent/init-env.json` — e2e framework, ports, services
6. **Optional:** `outbid-test-manifest.yaml` — test infrastructure and commands

## Step 2: Analyze the Repo

Explore the repository structure relevant to the feature. Understand:
- Project language and framework
- Existing patterns and conventions
- File organization
- Available test infrastructure

## Step 3: Create the Plan

Write `.dirigent/PLAN.json` with this exact format:

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
          "test_level": "L1"
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
9. If `outbid-test-manifest.yaml` exists: only use test commands defined there
10. If `init-env.json` shows e2e framework: plan e2e test tasks using that framework
