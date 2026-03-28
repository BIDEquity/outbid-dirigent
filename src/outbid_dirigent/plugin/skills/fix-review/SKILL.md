---
name: fix-review
description: Fix issues found during phase review (executor role in review loop)
arguments: none - review context provided via prompt
---

# Fix Review Findings

Fix all issues identified in the phase review. You are the EXECUTOR — you fix what the reviewer found.

## Role

Du bist der Executor. Der Reviewer hat Findings dokumentiert. Deine Aufgabe ist es, alle CRITICAL und WARN Findings zu fixen.

## Process

### Step 1: Read the Review

Read `.dirigent/reviews/phase-{PHASE_ID}-REVIEW.md` to understand all findings.

### Step 2: Prioritize

1. Fix all CRITICAL findings first
2. Fix all WARN findings
3. INFO findings are optional — only fix if trivial

### Step 3: Fix Each Finding

For each finding:
1. Navigate to the file and line mentioned
2. Understand the issue
3. Apply the fix
4. Verify the fix doesn't break anything

### Step 4: Commit

```bash
git add -A && git commit -m "fix(phase-{PHASE_ID}): post-review fixes"
```

### Step 5: Update Review Status

Write `.dirigent/reviews/phase-{PHASE_ID}-FIXES.md` documenting what was fixed:

```markdown
# Phase {PHASE_ID} Fixes

## Fixed Findings

| # | Original Finding | Fix Applied |
|---|-----------------|-------------|
| 1 | ... | ... |

## Skipped Findings

| # | Finding | Reason |
|---|---------|--------|
| 1 | ... | ... |
```

## Constraints

- Keine neuen Features einfuehren, nur Bugs fixen.
- Wenn der Review keine CRITICAL/WARN Findings hat, nichts tun.
- Jeder Fix muss minimal und fokussiert sein.
- Nicht mehr aendern als noetig um das Finding zu beheben.
