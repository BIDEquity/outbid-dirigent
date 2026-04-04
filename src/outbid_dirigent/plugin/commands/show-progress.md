---
name: show-progress
description: Show current execution progress (phases, tasks, status)
argument-hint: [--format console|text|json]
allowed-tools: Bash, Read, Glob
---

Show the current execution progress of the dirigent run.

## Files to read

1. `${DIRIGENT_RUN_DIR}/STATE.json` — progress state (completed tasks/phases)
2. `${DIRIGENT_RUN_DIR}/PLAN.json` — the full plan
3. `${DIRIGENT_RUN_DIR}/ROUTE.json` — route info
4. `${DIRIGENT_RUN_DIR}/contracts/` — contract status per phase
5. `${DIRIGENT_RUN_DIR}/reviews/` — review verdicts per phase

## Output

Default format is `console` unless `--format` is specified in $ARGUMENTS.

### Console format

Use a visual display with progress bars and status icons:
- Done tasks: checkmark
- Current task: hammer icon
- Pending: hourglass
- Include contract verdict per phase
- Show summary line: progress percentage, deviations, review results, duration

### Text format

Single-line compact: `Progress: X/Y tasks (Z%), N/M phases | Current: Phase P "name" — Task T "name" | Route: type | Duration: Xm Ys`

### JSON format

Structured JSON with phases, tasks, statuses, contract verdicts.
