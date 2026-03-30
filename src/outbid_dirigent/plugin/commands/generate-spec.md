---
name: generate-spec
description: Generate a SPEC.md from a user description, asking max 2-3 clarifying questions
allowed-tools: Bash, Read, Write, Glob, Grep, AskUserQuestion
---

Run the `generate-spec` skill from the dirigent plugin. Read `.dirigent/spec-seed.json` for the user's description and repo context, ask at most 2-3 clarifying questions, then write `.dirigent/SPEC.md`.
