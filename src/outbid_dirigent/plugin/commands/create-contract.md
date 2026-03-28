---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
argument-hint: <phase-id>
allowed-tools: Bash, Read, Write, Glob, Grep
---

Create an acceptance criteria contract for Phase $ARGUMENTS.

## Context files to read

1. `.dirigent/PLAN.json` — read the phase matching ID "$ARGUMENTS" to understand its tasks
2. `.dirigent/SPEC.md` — the feature spec for context
3. `outbid-test-manifest.yaml` — test commands available for verification (if exists)

Follow the SKILL.md instructions to create `.dirigent/contracts/phase-$ARGUMENTS-CONTRACT.md`.
