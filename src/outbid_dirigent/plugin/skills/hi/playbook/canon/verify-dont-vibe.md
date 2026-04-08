# Verify, don't vibe

**Track:** Agent rule (enforced in `implement-task`, `review-phase`, `fix-review`)

**Thesis:** "The LLM thinks it works" is not evidence. Every task needs a runtime gate that actually executes. If the executor can't run the app, contracts can only claim *structural* correctness — and must say so explicitly.

## The incident

A real migration run on a complex Rails app produced code that was "mostly in the right places" but with invalid Ruby syntax and no runtime verification. The executor couldn't boot the app — complex DB and service setup — so it added code blind. The behavioral verification commands in the contract were useless because the app wasn't running. Structural checks (`ruby -c`) would have caught the bad syntax instantly, but weren't part of the gate.

The lesson: **structural verification is not optional, even when behavioral verification is impossible.** If you can't curl the endpoint, you can still syntax-check the file. If you can't run the tests, you can still typecheck. If you can't boot the app, you can still lint.

## The rule

Every task execution must include at least one of these gates before committing:

- **Ideal:** runtime check — `curl localhost`, `pytest -x`, `npm test`, `cargo run`. Actually exercise the code.
- **Acceptable fallback:** structural check — `ruby -c`, `tsc --noEmit`, `ruff check`, `go vet`, `cargo check`. Prove the code at least parses and types.
- **Minimum:** syntax parse of every file the task touched. Zero-tolerance for committing files that don't parse.

If the contract asks for behavioral verification and the executor cannot run the app, the reviewer **must** downgrade the criterion to structural-only and state so explicitly in the review. No pretending. No "it looks right to me." No evidence, no pass.

## How to apply

- **Executor:** before committing, run whatever gate is available. If nothing works, flag it as a deviation with the reason and the best structural check you did run.
- **Reviewer:** behavioral criteria without evidence = fail. Structural criteria may pass based on tool output alone. Never fabricate evidence.
- **Contract author:** if the repo can't bootstrap the app, *write structural contracts*. Don't write curl-based contracts for environments where curl will never run.

## Enforced in

- `skills/implement-task/SKILL.md` — Contract awareness + convention skills block.
- `skills/review-phase/SKILL.md` — "You MUST run the actual command and record the output as evidence. A 'pass' verdict without evidence for behavioral/boundary criteria is INVALID."
- `skills/fix-review/SKILL.md` — Fixes must satisfy the contract criteria that were flagged failed.
