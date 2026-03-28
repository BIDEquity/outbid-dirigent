---
name: review-phase
description: Review code changes from a completed phase against acceptance criteria (reviewer role)
argument-hint: <phase-id> --commits <n> [--iteration <n>]
allowed-tools: Bash, Read, Write, Glob, Grep
---

Review Phase $ARGUMENTS against its contract.

## Context files to read

1. `.dirigent/contracts/phase-{PHASE_ID}-CONTRACT.md` — the acceptance criteria to check against
2. `.dirigent/PLAN.json` — phase and task details

Parse the phase-id from $ARGUMENTS (first word). Use `--commits` value for `git diff HEAD~N`.

Follow the SKILL.md instructions. Write your review to `.dirigent/reviews/phase-{PHASE_ID}-REVIEW.md`. The review MUST contain a clear `## Contract Verdict: PASS` or `## Contract Verdict: FAIL` line.

**CRITICAL: You are the REVIEWER. Do NOT modify any code. Only read and review.**
