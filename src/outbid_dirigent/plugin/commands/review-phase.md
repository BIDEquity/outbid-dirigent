---
name: review-phase
description: Review code changes from a completed phase against acceptance criteria (reviewer role)
argument-hint: <phase-id> --commits <n> [--iteration <n>]
allowed-tools: Bash, Read, Write, Glob, Grep
---

Review Phase $ARGUMENTS against its contract.

Parse the phase-id (first word), `--commits` (for `git diff HEAD~N`), and `--iteration` from $ARGUMENTS.

Read the contract from `.dirigent/contracts/phase-{PHASE_ID}.json`. Follow the SKILL.md instructions to write `.dirigent/reviews/phase-{PHASE_ID}.json` — valid JSON only, no markdown.

**You are the REVIEWER. Do NOT modify any code. Only read and evaluate.**
