---
name: add-posthog
description: Analyze the app and produce a PostHog tracking instrumentation plan
argument-hint: (no arguments needed)
allowed-tools: Bash, Read, Write, Glob, Grep
---

Analyze this application and produce a PostHog tracking instrumentation plan.

If `.dirigent/SPEC.md` exists, read it for context on which features to track.

Follow the SKILL.md instructions to detect the tech stack, identify key user flows, and write `.dirigent/tracking-plan.json` — valid JSON only.
