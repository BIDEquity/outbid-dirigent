---
name: generate-architecture
description: Generate ARCHITECTURE.md for the target repository — a complete, agent-readable map of the codebase
argument-hint: [--update]
allowed-tools: Bash, Read, Write, Glob, Grep
---

Run the `generate-architecture` skill from the dirigent plugin. Analyze the repository structure, modules, data flow, and key design patterns, then write `ARCHITECTURE.md` at the repo root.

Use `--update` to refresh an existing ARCHITECTURE.md while preserving manually-written sections.
