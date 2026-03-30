---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
argument-hint: <phase-id>
allowed-tools: Bash, Read, Write, Glob, Grep
---

Create an acceptance criteria contract for Phase $ARGUMENTS using three layers: structural (~20%), behavioral (~60%), and boundary (~20%).

Read `.dirigent/PLAN.json` to find the phase, `.dirigent/SPEC.md` for context, and `.dirigent/test-harness.json` for verification methods. Behavioral criteria MUST test user-facing behavior via HTTP calls or test runners — not grep on source files.

Follow the SKILL.md instructions to write `.dirigent/contracts/phase-$ARGUMENTS.json` — valid JSON only, no markdown.
