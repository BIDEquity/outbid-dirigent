---
name: run-init
description: Run init script to bootstrap dev environment for e2e testing
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Glob, Grep
---

Bootstrap the development environment by discovering and running init scripts.

Follow the SKILL.md instructions to:
1. Find `.outbid/init.sh` or `init.sh`
2. Execute it
3. Capture environment state (ports, services, e2e credentials)
4. Write `.dirigent/INIT_REPORT.md`
