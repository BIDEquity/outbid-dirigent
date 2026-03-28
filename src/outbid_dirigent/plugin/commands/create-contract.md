---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
argument-hint: <phase-id>
allowed-tools: Bash, Read, Write, Glob, Grep
---

Create an acceptance criteria contract for Phase $ARGUMENTS.

Read `.dirigent/PLAN.json` to find the phase, `.dirigent/SPEC.md` for context, and `.dirigent/test-harness.json` if it exists.

Follow the SKILL.md instructions to write `.dirigent/contracts/phase-$ARGUMENTS.json` — valid JSON only, no markdown.
