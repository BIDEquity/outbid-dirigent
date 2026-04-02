---
name: create-contract
description: Create acceptance criteria contract for a phase before execution
argument-hint: <phase-id>
allowed-tools: Bash, Read, Write, Glob, Grep
---

Create an acceptance criteria contract for Phase $ARGUMENTS.

Read `.dirigent/PLAN.json` to find the phase, `.dirigent/SPEC.md` for context, and `.dirigent/test-harness.json` for verification methods.

Follow the SKILL.md instructions to write `.dirigent/contracts/phase-$ARGUMENTS.json`.

**CRITICAL — the output JSON is validated by a strict Pydantic schema. Use EXACTLY these field names or the contract will be silently rejected:**
- Root fields: `phase_id`, `phase_name`, `objective`, `acceptance_criteria`, `quality_gates`, `out_of_scope`, `expected_files`
- Per criterion: `id` (format: AC-{PHASE_ID}-NN), `description`, `verification` (starts with "Run: "), `layer`
- Max 8 criteria total. Output ONLY valid JSON, no markdown.
