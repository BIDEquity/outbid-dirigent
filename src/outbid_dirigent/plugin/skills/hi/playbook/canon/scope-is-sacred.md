# Scope is sacred

**Track:** Agent rule (enforced in `implement-task` skill, and in `implementer` agent — including its Review-Fix Mode)

**Thesis:** The agent implements the task. Not the task *and* nearby cleanup. Not the task *and* speculative abstractions. Not the task *and* "while I was here, I noticed…" Just the task.

## The rule

- No features beyond what the SPEC says.
- No refactoring neighboring code that wasn't part of the task.
- No "I'll just also fix this other thing" — log it as a follow-up, don't do it.
- No adding error handling, fallbacks, or validation for scenarios that can't happen.
- No configurability, feature flags, or "in case we need this later" hooks.
- No backwards-compatibility shims when the change is a clean break.

## Why it matters

Scope drift is the single most expensive failure mode of agent-driven development. It's expensive because it's *invisible* — the PR looks bigger but not obviously wrong, so review takes longer, regressions hide in unrelated changes, and rollback requires unpicking work that shouldn't have been there.

Worse, scope drift trains the user to distrust the agent. Every time you open a PR and find 14 files changed when you asked for 2, you spend cycles verifying the other 12. Trust compounds. So does its absence.

The global rule in CLAUDE.md already says this plainly: *"Don't add features, refactor code, or make 'improvements' beyond what was asked. A bug fix doesn't need surrounding code cleaned up."* The canon version is just the *why*, loud enough that it sticks.

## How to apply

- If a task description says "add endpoint X," add endpoint X. Do not also update the logger, normalize the error responses, or "while I'm here" extract a helper.
- If you notice a real bug in code you're touching, note it as a `DEVIATION: Bug-Fix` with a description — do not silently expand scope.
- Three similar lines of code are better than a premature abstraction. Do not extract a helper for one-time operations.
- If you genuinely need to touch unrelated code to make the task work, say so explicitly in the deviation log with the reason.

## Enforced in

- `skills/implement-task/SKILL.md` — Constraints: "Stick to the task description. Do not add unrelated features."
- `agents/implementer.md` (Review-Fix Mode) — Constraint: fix only what the reviewer flagged.
- `agents/reviewer.md` — Reviewers flag unexpected scope expansion as a finding.
