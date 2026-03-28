---
name: fix-review
description: Fix issues found during phase review (executor role)
---

# Fix Review Findings

You are the EXECUTOR. The reviewer identified issues. Your job is to fix them.

## Process

### Step 1: Read the Review

Read `.dirigent/reviews/phase-{PHASE_ID}-REVIEW.md` for all findings.

### Step 2: Prioritize

1. Fix all **CRITICAL** findings first
2. Fix all **WARN** findings
3. **INFO** findings are optional — only fix if trivial

### Step 3: Fix Each Finding

For each finding:
1. Navigate to the file and line
2. Understand the issue
3. Apply a minimal, focused fix
4. Verify the fix doesn't break anything

### Step 4: Commit

```bash
git add -A && git commit -m "fix(phase-{PHASE_ID}): review fixes iteration {N}"
```

### Step 5: Report

Write `.dirigent/reviews/phase-{PHASE_ID}-FIXES.md`:

```markdown
# Phase {PHASE_ID} Fixes

## Fixed Findings

| # | Original Finding | Fix Applied |
|---|-----------------|-------------|
| 1 | ... | ... |

## Skipped Findings

| # | Finding | Reason |
|---|---------|--------|
```

## Constraints

- No new features. Only bug fixes.
- If no CRITICAL/WARN findings exist, do nothing.
- Each fix must be minimal — don't change more than needed.
