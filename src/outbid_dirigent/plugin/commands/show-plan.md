---
name: show-plan
description: Display the current execution plan in a readable format
argument-hint: [--format console|text|json]
allowed-tools: Read
---

Display the current execution plan from `${DIRIGENT_RUN_DIR}/PLAN.json`.

Read the plan file and format it based on `--format` in $ARGUMENTS (default: console).

### Console format

Structured display with phase headers, task details (name, model, effort, files), assumptions, out-of-scope, and risks.

### Text format

Compact one-line-per-task: `Phase ID: Name` → `  Task-ID: Task-Name [model]`

### JSON format

Raw PLAN.json content.
