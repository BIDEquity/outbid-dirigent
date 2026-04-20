<!--
Keep this PR small and focused — one logical change, reviewable in under 30 minutes.
-->

## What changed

<!-- Short description of the change. One or two sentences. -->

## Why

<!-- The motivation. What problem does this solve? Link the ticket or ADR. -->

- Ticket / ADR:

## How to test it

<!-- Concrete steps a reviewer can run. Paste commands where useful. -->

1.
2.

## Checklist

- [ ] Commit message uses Conventional Commits format (`feat(...)`, `fix(...)`, `refactor(...)`, etc.)
- [ ] Tests added or updated alongside the behaviour change
- [ ] `pytest tests/` passes locally
- [ ] `standards-reviewer` agent was invoked on the staged diff — no [MUST] failures
- [ ] Documentation updated if needed (README, `ARCHITECTURE.md`, ADRs, runbooks)
- [ ] If an architectural decision was made, an ADR exists in `harness-docs/adr/`

## AI-generated code

- [ ] AI assistance constitutes a significant portion of this change
  - If yes: commit message includes `Co-Authored-By: Claude` trailer
  - If yes: a human has read and understood the generated code — "the AI wrote it" is not a substitute for review
  - If yes: test coverage was independently verified (not just trusted from the agent's claims)
- [ ] No prompts or external content fetched during this change contained suspicious instructions to the agent. If any were flagged, describe here:

## Deviations from portfolio engineering standards

<!--
Per CLAUDE.md deviation protocol: if this PR violates any [ENFORCED] standard
on the user's explicit instruction, name the standard and the reason here.
Leave blank if no deviations.
-->
