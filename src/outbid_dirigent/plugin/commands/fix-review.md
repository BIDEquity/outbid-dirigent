---
name: fix-review
description: Fix issues found during phase review (executor role)
argument-hint: <phase-id> [--iteration <n>]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Fix all critical and warn findings from the review of Phase $ARGUMENTS.

Parse the phase-id (first word) and `--iteration` from $ARGUMENTS.

Read the review from `.dirigent/reviews/phase-{PHASE_ID}.json` and the contract from `.dirigent/contracts/phase-{PHASE_ID}.json`. Follow the SKILL.md instructions.

If no critical or warn findings exist, do nothing.
