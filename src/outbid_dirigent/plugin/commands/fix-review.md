---
name: fix-review
description: Fix issues found during phase review (executor role)
argument-hint: <phase-id> [--iteration <n>]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Fix all CRITICAL and WARN findings from the review of Phase $ARGUMENTS.

## Context files to read

1. `.dirigent/reviews/phase-{PHASE_ID}-REVIEW.md` — the review findings to fix

Parse the phase-id from $ARGUMENTS (first word). Parse `--iteration` if present.

Follow the SKILL.md instructions. After fixing, commit with `git add -A && git commit -m "fix(phase-{PHASE_ID}): review fixes iteration {N}"` and write `.dirigent/reviews/phase-{PHASE_ID}-FIXES.md`.

If no CRITICAL/WARN findings exist in the review, do nothing.
