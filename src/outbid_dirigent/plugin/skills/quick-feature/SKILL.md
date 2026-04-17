---
name: quick-feature
description: Implement a small feature end-to-end — plan, implement, review — using focused subagents. Use for changes that fit in 1-3 files.
disable-model-invocation: true
---

# Quick Feature

Orchestrate three subagents in sequence: plan → implement → review. You do not write code. You dispatch, read artifacts, and report.

**Input:** `$ARGUMENTS` — a short description of what to build.

## Scope Check FIRST — Is This Actually Quick?

Before dispatching anything, read `$ARGUMENTS` and check the redirect triggers. If ANY match, stop and tell the user to use `/dirigent:start` (the full pipeline with contract + phased plan + oracle):

| Trigger | Why quick won't fit |
|---|---|
| Touches more than 3 files | No phase boundary, reviewer can't hold context |
| Adds a new runtime dependency | Needs architecture review — goes in ARCHITECTURE.md |
| Schema change / DB migration | Needs a contract with rollback criteria |
| Cross-cutting refactor (rename across package, lift abstraction) | Blast radius > 1 reviewer pass |
| New public API / breaking change | Needs AC negotiation, not a reviewer spot-check |
| "Also fix X while you're there" (two features) | Split into two quick runs or use full pipeline |
| User can't describe it in 1-2 sentences | Scope is not compressed — plan it first |

If none match, proceed. If in doubt, lean toward redirect — quick fails silently on over-scoped work.

## Steps At A Glance

| # | Step | Agent | Input | Output |
|---|---|---|---|---|
| 1 | Plan | `infra-architect` | `$ARGUMENTS` + live repo | `${DIRIGENT_RUN_DIR}/quick-plan.md` |
| 2 | Implement | `implementer` | quick-plan.md contents | git commits + `${DIRIGENT_RUN_DIR}/summaries/quick-feature-SUMMARY.md` |
| 3 | Review | `reviewer` | quick-plan.md + recent commits | `${DIRIGENT_RUN_DIR}/reviews/quick-feature.json` |

## Step 1: Plan

Dispatch the `infra-architect` agent with this prompt:

> Read the codebase structure. The user wants: "$ARGUMENTS"
>
> Write a brief plan to `${DIRIGENT_RUN_DIR}/quick-plan.md` with:
> - **Files to create or modify** (absolute paths, be specific — if you list more than 3, STOP and return "scope too large, redirect to full pipeline")
> - **Test files** to create or modify (EVERY new function/endpoint MUST have tests — no exceptions)
> - **What each change does** (1-2 sentences per file, not prose)
> - **Verification commands** the reviewer can run — MUST include the test command and MUST produce non-empty output on success
> - **Acceptance criteria** as a short list, IDs `QF-01`, `QF-02`, ... — one line each, testable
>
> No architecture essays. No phase breakdown. If you can't fit it on one screen, the scope is too large — return that verdict.

After the agent returns, read `${DIRIGENT_RUN_DIR}/quick-plan.md`. If it says "scope too large", stop and tell the user to use `/dirigent:start`.

## Step 2: Implement

Dispatch the `implementer` agent with this prompt:

> Implement the following plan. One commit per logical change (e.g. `feat: add X`, then `test: cover X`). Use Conventional Commits: `feat:` / `fix:` / `test:` / `refactor:` / `docs:`.
>
> {paste the full contents of ${DIRIGENT_RUN_DIR}/quick-plan.md}
>
> Constraints:
> - Implement ONLY what the plan lists. Do not refactor adjacent code. Do not "improve" what you didn't touch.
> - Every new function/endpoint gets a test in the same commit series.
> - Run the full test suite after your changes. If anything fails, fix it or revert — do not commit failing code.
> - Write a summary to `${DIRIGENT_RUN_DIR}/summaries/quick-feature-SUMMARY.md` with: files changed, commits made (SHAs + titles), test output excerpt.

After the agent returns, verify the summary file exists. If it doesn't, the implementer crashed — report the error, do not retry.

## Step 3: Review

Dispatch the `reviewer` agent with this prompt:

> Review the most recent commits on this branch against the plan below.
>
> {paste the full contents of ${DIRIGENT_RUN_DIR}/quick-plan.md}
>
> Run every verification command from the plan. Run the full test suite. Check that each `QF-nn` acceptance criterion is met.
>
> Verdict rules:
> - Any test fails → `fail`
> - New functionality without a test → `fail` (not "warn")
> - Scope drift (files touched that aren't in the plan) → `fail`
> - Otherwise → `pass`
>
> Write your review to `${DIRIGENT_RUN_DIR}/reviews/quick-feature.json`:
>
> ```json
> {
>   "phase_id": "quick",
>   "iteration": 1,
>   "verdict": "pass",
>   "criteria_results": [
>     {"ac_id": "QF-01", "verdict": "pass", "notes": "...", "evidence": [{"command": "...", "exit_code": 0, "stdout_snippet": "..."}]}
>   ],
>   "findings": [],
>   "summary": "..."
> }
> ```

Read the review. If `pass`, report success + commit SHAs. If `fail`, report findings verbatim — do not attempt repairs.

## Anti-Patterns

| Don't | Why |
|---|---|
| Implement code yourself "just this small bit" | You lack the subagent's fresh context; you'll conflate plan with execution |
| Skip review because "it's a one-liner" | One-liners are where silent regressions live — review is cheap |
| Retry a failed implementer with a tweaked prompt | Failure means the plan or scope is wrong; redirect to full pipeline |
| Auto-fix reviewer findings in-line | Turns quick into an uncontrolled loop; surface findings, let user decide |
| Let the implementer refactor adjacent code | Scope drift — reviewer will fail it, wasting a full round-trip |
| Accept a plan with >3 files | Quick's contract assumes reviewer can hold it all in one pass |

## Rules

<rules>
<rule>Run the Scope Check BEFORE Step 1 — redirecting early costs one message; redirecting after implementation costs a revert.</rule>
<rule>Do NOT implement anything yourself — delegate every code change to the subagents. The orchestrator's job is dispatch + read + report, nothing else.</rule>
<rule>Do NOT skip review — even a one-line change goes through Step 3. Review is the only gate catching scope drift and missing tests.</rule>
<rule>If the implementer fails, report the error and stop — do not retry with a modified prompt. Failure = scope is wrong, escalate.</rule>
<rule>If the reviewer returns `fail`, report findings verbatim and stop — do not auto-dispatch a fix. The user decides whether to retry or redirect.</rule>
<rule>Plans with >3 files or a new dependency are not quick — return the redirect verdict in Step 1 rather than proceeding.</rule>
<rule>Every new function/endpoint needs a test in the same commit series — no "will add tests later", ever.</rule>
<rule>Commits follow Conventional Commits (`feat:` / `fix:` / `test:` / `refactor:` / `docs:`) — this is how the reviewer and downstream tooling group changes.</rule>
</rules>

<constraints>
<constraint>Output: git commits on the current branch + `quick-plan.md` + `quick-feature-SUMMARY.md` + `quick-feature.json` (last three in `${DIRIGENT_RUN_DIR}`).</constraint>
<constraint>No phase directories, no contract files, no oracle — if you need those, you're in the wrong route.</constraint>
</constraints>
