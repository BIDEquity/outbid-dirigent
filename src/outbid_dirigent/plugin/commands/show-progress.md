---
name: show-progress
description: Show current execution progress (phases, tasks, status)
argument-hint: [--format console|text|json]
allowed-tools: Bash, Read, Glob
---

Show the current execution progress of the dirigent run.

## Steps

1. Read `.dirigent/STATE.json` for progress state
2. Read `.dirigent/PLAN.json` for the full plan
3. Read `.dirigent/ROUTE.json` for route info
4. Check `.dirigent/contracts/` for contract status
5. Check `.dirigent/reviews/` for review status

## Output Format

### Console (default, or --format console)

```
═══════════════════════════════════════════════════
  OUTBID DIRIGENT — Progress Report
═══════════════════════════════════════════════════

  Route: hybrid (3 steps remaining)
  Plan:  "Feature Title" (3 phases, 9 tasks)

  Phase 01: Setup Foundation          ████████████ DONE
    ✅ 01-01  Create base models
    ✅ 01-02  Setup API routes
    ✅ 01-03  Add database migration
    📋 Contract: PASS (3/3 criteria met)

  Phase 02: Implement Logic           ██████░░░░░░ IN PROGRESS
    ✅ 02-01  Add validation rules
    🔨 02-02  Implement business logic    ← current
    ⏳ 02-03  Add error handling
    📋 Contract: PENDING

  Phase 03: Testing & Polish          ░░░░░░░░░░░░ PENDING
    ⏳ 03-01  Write unit tests
    ⏳ 03-02  Add integration tests
    ⏳ 03-03  Final cleanup

  ─────────────────────────────────────────────────
  Progress: 4/9 tasks (44%) | 1/3 phases done
  Deviations: 2 | Reviews: 1 pass, 0 fail
  Duration: 12m 34s
═══════════════════════════════════════════════════
```

### Text (--format text)

Plain text summary suitable for logs:

```
Progress: 4/9 tasks (44%), 1/3 phases complete
Current: Phase 02 "Implement Logic" — Task 02-02 "Implement business logic"
Route: hybrid | Duration: 12m 34s | Deviations: 2
```

### JSON (--format json)

Output as structured JSON for programmatic consumption.
