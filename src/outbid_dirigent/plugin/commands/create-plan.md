---
name: create-plan
description: Create a phased execution plan (PLAN.json) from spec and repo context
argument-hint: [<description>] [--yolo]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

Create an execution plan. If `.dirigent/SPEC.md` exists, use it. Otherwise, use `$ARGUMENTS` as the feature description and generate a short spec first (asking max 2-3 clarifying questions, or zero with `--yolo`).

Follow the SKILL.md instructions.
