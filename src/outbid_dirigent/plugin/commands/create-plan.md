---
name: create-plan
description: Create a phased execution plan (PLAN.json) from spec and repo context
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Glob, Grep
---

Create an execution plan for the feature described in `.dirigent/SPEC.md`.

## Context files to read

1. `.dirigent/SPEC.md` — the feature spec (REQUIRED)
2. `.dirigent/BUSINESS_RULES.md` — business rules to preserve (if exists, Legacy route)
3. `.dirigent/CONTEXT.md` — relevant repo context (if exists, Hybrid route)
4. `.dirigent/test-harness.json` — e2e test harness (if exists)

Read all available context files first, then follow the SKILL.md instructions to create `.dirigent/PLAN.json`.
