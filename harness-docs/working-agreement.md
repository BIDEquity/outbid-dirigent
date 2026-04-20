# Working Agreement — Outbid Dirigent

**Last Reviewed:** 2026-04-20
**Next Review:** 2026-07-20 (quarterly)

## Team Context

Outbid Dirigent is maintained by a solo owner (Jonah Kresse) working alongside
AI agents (Claude Code, subagents). Many traditional working-agreement sections
assume a multi-engineer team — this document adapts them to a solo-maintainer-
plus-agents context. The agreement still applies: it governs how work gets from
idea to merged code, regardless of whether the co-worker is human or an agent.

## Meeting Cadences

| Meeting | Frequency | Purpose |
|---|---|---|
| Self-retro | Monthly | Review what shipped, what broke, what agent behaviours need CLAUDE.md updates |
| Quarterly review | Quarterly | Re-run `/assess`, update this agreement and `CLAUDE.md`, audit stale memory |

Standups, sprint planning, and refinement are intentionally omitted — not
applicable for a single-maintainer project. If the team grows, reinstate them.

## Communication Norms

- **Issue tracker / backlog:** ClickUp (see user-level memory for project references).
- **PR discussion:** GitHub PR comments.
- **Agent instructions:** `CLAUDE.md` at repo root. If an agent produces
  unexpected output, update `CLAUDE.md` in the same PR that corrects the output
  — not in a follow-up.

## Definition of Done

A change is "done" when ALL of the following are true:

- [ ] Code reviewed (human or agent) — no self-merge of feature work without review
- [ ] All tests passing (unit + integration; E2E where applicable)
- [ ] Tests added or updated alongside behaviour changes
- [ ] Structured reviewer invoked (`standards-reviewer` agent on the staged diff)
- [ ] Feature toggled if user-facing and incremental — N/A for this CLI
- [ ] Documentation updated — README, `ARCHITECTURE.md`, ADRs, runbooks as needed
- [ ] If AI-generated code is a significant portion of the change, flagged via
      `Co-Authored-By: Claude` trailer in the commit message
- [ ] Conventional Commits format used for the commit message
- [ ] If an architectural decision was made, an ADR exists in `harness-docs/adr/`

## On-Call Expectations

**N/A.** Dirigent is a CLI tool and Python package — no production runtime
service, no on-call rotation. If a breaking defect ships to users, the fix
follows the normal DoD process (no emergency shortcut).

If this repo ever grows a hosted component, reinstate on-call norms before
shipping that component.

## Decision-Making

- **Day-to-day technical decisions:** Maintainer's call.
- **Architectural decisions:** Documented as ADRs in `harness-docs/adr/`
  using `/adr`. ADRs are created before or alongside the change that makes
  the decision load-bearing — not after.
- **Deviations from portfolio engineering standards:** Follow the deviation
  protocol in `CLAUDE.md` (comply with the explicit instruction, flag the
  deviation and reason in the PR description).

## Code Review Norms

- Every PR gets at least one review pass before merge — either from a human
  reviewer or from an agent-driven review (e.g. `/bid-harness:code-review`,
  `pr-review-toolkit:code-reviewer`, or `standards-reviewer`). Self-merge
  without a review pass is not allowed for feature work.
- Use [Conventional Comments](https://conventionalcomments.org/) style: labels
  (`nit:`, `issue:`, `question:`, `suggestion:`) make intent legible and avoid
  ambiguity.
- Approve with minor comments rather than blocking on style nits.
- Stale PRs (> 3 days without activity) get resolved: merge, revise, or close.
- **AI-generated code:** treat the agent as the author under review. Do not
  rely on the agent to write and self-approve its own tests; verify coverage
  independently.

## Retrospectives

Monthly self-retro covers, at minimum:
- What shipped? What broke?
- Did any agent produce unexpected output? If so, was `CLAUDE.md` updated in
  the same PR that corrected it?
- Any recurring guidance the user had to repeat to agents? If so, save as a
  feedback memory so it sticks.

Retro action items get tracked in ClickUp with an owner (always the
maintainer here) and a due date.

## Review and Update

This agreement is reviewed quarterly. If a change would materially alter how
work is done (e.g. a second maintainer joins, production runtime added,
different agent workflow adopted), update this document in the same PR that
makes the change.
