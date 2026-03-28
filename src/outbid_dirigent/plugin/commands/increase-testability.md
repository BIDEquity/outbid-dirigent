---
name: increase-testability
description: Analyze testability gaps and show concrete ways to improve the testability score
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Glob, Grep
---

Analyze the current testability of this project and produce actionable recommendations to increase the testability score.

Read `.dirigent/test-harness.json` for the current score and gaps, then inspect the repo for additional opportunities.

Follow the SKILL.md instructions to write `.dirigent/testability-recommendations.json` — valid JSON only.
