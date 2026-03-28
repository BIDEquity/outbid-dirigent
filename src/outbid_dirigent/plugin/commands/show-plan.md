---
name: show-plan
description: Display the current execution plan in a readable format
argument-hint: [--format console|text|json]
allowed-tools: Read
---

Display the current execution plan from `.dirigent/PLAN.json`.

## Steps

1. Read `.dirigent/PLAN.json`
2. Format and display based on --format argument

## Output Format

### Console (default)

```
═══════════════════════════════════════════════════
  PLAN: {title}
═══════════════════════════════════════════════════

  Summary: {summary}
  Complexity: {estimated_complexity}
  Phases: {count} | Tasks: {count}

  ─── Phase 01: {name} ───
  {description}

    01-01  {task_name}                    [sonnet/medium]
           {task_description}
           Create: {files_to_create}
           Modify: {files_to_modify}

    01-02  {task_name}                    [haiku/low]
           ...

  ─── Phase 02: {name} ───
  ...

  Assumptions:
    • {assumption_1}
    • {assumption_2}

  Out of Scope:
    • {item_1}

  Risks:
    ⚠ {risk_1}
═══════════════════════════════════════════════════
```

### Text (--format text)

Compact one-line-per-task format suitable for logs.

### JSON (--format json)

Raw PLAN.json content.
