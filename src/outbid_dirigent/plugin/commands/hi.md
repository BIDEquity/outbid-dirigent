---
name: hi
description: The Dirigent coach — onboarding, playbook, and daily-driver entry point
argument-hint: [optional: what do you want to build?]
allowed-tools: Read, Bash, Glob, Grep, Edit, Write, Skill
---

Invoke the `hi` skill to enter the Dirigent coach. This is the main entry point for both new users (onboarding) and veterans (daily driver).

If `$ARGUMENTS` contains a natural-language intent, pass it through — the coach will classify it and route to the right sibling skill. If `$ARGUMENTS` is empty, the coach will detect repo state and open in the matching mode (onboarding / continue / resume / recovery / coach).

Use the Skill tool to invoke `hi` with `$ARGUMENTS` as the skill input.
