---
name: run-init
description: Inspect repo and produce test harness specification for e2e verification
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Glob, Grep
---

Inspect this repository and produce a test harness specification.

If `.dirigent/init-output.log` exists, read it — it contains output from an init script that already ran. If `.dirigent/init-new-env.json` exists, read it for env vars the init script exported.

Follow the SKILL.md instructions to analyze the repo's tech stack, auth system, seed data, and e2e framework, then write `.dirigent/test-harness.json` — valid JSON only.
