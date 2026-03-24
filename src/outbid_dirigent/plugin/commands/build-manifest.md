---
name: build-manifest
description: Analyze the repo and generate outbid-test-manifest.yaml with test infrastructure and preview config
argument-hint: [--interactive]
allowed-tools: Bash, Read, Write, Glob, Grep
---

Run the `build-manifest` skill from the dirigent plugin. Read the skill's `schema.py`, `schema.json`, and `example.yaml` reference files first, then follow the SKILL.md instructions to analyze this repo and generate `outbid-test-manifest.yaml`.

Pass `--interactive` to walk through each section (prerequisites, components, test levels, gaps, preview) with the user before writing.
