---
name: entropy-minimization
description: Align code and documentation, remove dead code, resolve contradictions after execution
argument-hint: [--scope full|changed]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

Run the `entropy-minimization` skill from the dirigent plugin. Scan the repository for entropy accumulated during execution — stale documentation, dead code, contradictions between code and docs, unused imports, orphaned references — and fix everything found. Commit fixes atomically.

Default scope is `changed` (only files touched in recent commits). Use `--scope full` to scan the entire repository.
