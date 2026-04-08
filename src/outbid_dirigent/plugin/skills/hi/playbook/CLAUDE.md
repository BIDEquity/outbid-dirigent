# Dirigent playbook primer

> **How to use this file:** Drop it in any repo where you intend to use Dirigent. Claude Code auto-loads `CLAUDE.md` on session start, so the playbook rules below apply to *every* session in that repo without anyone typing `/dirigent:hi`. You can also `@`-import this file from a parent `CLAUDE.md` if you want to keep yours focused on project-specific context.
>
> The full playbook lives in the dirigent plugin under `skills/hi/playbook/canon/` — read those files when you want the *why*, not just the *what*.

## When to use Dirigent (and when not)

**Use Dirigent for:**
- Features you can describe in a SPEC — scoped, testable, finite.
- Legacy migrations: large, repetitive, rule-driven.
- Adding test coverage, tracking, scaffolding — boilerplate-heavy work.
- "I'll be at lunch, here's the spec." Long-running, resumable, atomic-commit work.

**Do NOT use Dirigent for:**
- One-line tweaks. Writing the SPEC costs more than the change.
- Exploratory spikes or "I don't know what I want yet." Use plain Claude Code interactively until the answer is clear.
- Debugging ghosts where you need fast feedback in your head, not a headless loop.

The test: *can I write the acceptance criteria right now without thinking?* Yes → Dirigent. No → interactive mode first.

## The seven rules (apply silently, don't narrate unless asked)

1. **Spec first.** The SPEC is the cheapest place to fight scope battles. Every battle skipped there is paid for at 2× cost mid-execution. If a feature touches more than one file, write a SPEC — even a 10-line one beats none.
2. **Scope is sacred.** Implement *only* the task. No "while I was here" cleanup. No speculative abstractions. No features beyond the SPEC. Notice a real bug? Log it as a `DEVIATION: Bug-Fix`, do not silently expand scope.
3. **Verify, do not vibe.** Before committing any change, run a structural gate (`tsc --noEmit`, `ruff check`, `ruby -c`, `cargo check`, `pytest -x` — whatever fits the stack). "The LLM thinks it works" is not evidence. If the app can't boot, contracts can only claim *structural* correctness — say so explicitly.
4. **Read before you write.** Never edit a file you have not read in this session. Never reference a function, import path, or type you have not confirmed exists. Grep + Read is cheaper than a revert, every time.
5. **No sycophancy.** Do not say "you are absolutely right." Push back with evidence when warranted. Agreement without verification is a failure mode. If the user is wrong, say so and cite the code.
6. **Atomic commits per task.** Each task = one commit. Bisectability, rollback surface, and review sanity all depend on this. Do not bundle. Do not squash before review.
7. **Scratch state hygiene.** Never commit `.dirigent/`, `.dirigent-onboarding/`, `.planning/`, `.brv/`, or any scratch dir into the repo. Workspace is not deliverable. The plugin's `.gitignore` covers these by default — verify on every new repo.

## Discoverable surfaces (no need to memorize commands)

The dirigent plugin exposes its state through Claude Code's built-in surfaces, so you don't need to remember slash commands:

- **Statusline** — the bottom of every Claude Code session shows current dirigent phase/task, token usage (color-coded, warns at 70% / 90%), and git branch. If you see `🔴 ... — /clear soon`, do that.
- **SessionStart hook** — when you open a Claude session in a dirigent-shaped repo, the agent already knows your state (no plan / plan ready / run in progress / recovery needed) and opens with the right framing.
- **MCP resources** — the agent can read `dirigent://spec`, `dirigent://plan`, `dirigent://state`, `dirigent://progress`, `dirigent://summaries` directly, anytime, without you typing anything.
- **Slash commands** for explicit control: `/dirigent:hi` (the coach + onboarding + playbook), `/dirigent:show-plan`, `/dirigent:show-progress`.

## The full canon

For the *why* behind each rule, read the canon files in the plugin:

- `skills/hi/playbook/canon/spec-first-or-suffer.md`
- `skills/hi/playbook/canon/scope-is-sacred.md`
- `skills/hi/playbook/canon/verify-dont-vibe.md`
- `skills/hi/playbook/canon/read-before-you-write.md`
- `skills/hi/playbook/canon/no-sycophancy-rule.md`
- `skills/hi/playbook/canon/atomic-commits-per-task.md`
- `skills/hi/playbook/canon/scratch-state-hygiene.md`
- `skills/hi/playbook/canon/when-not-to-use-dirigent.md`
- `skills/hi/playbook/canon/ultrathink-as-a-ritual.md`
- `skills/hi/playbook/canon/domain-context-beats-orchestration.md`

And for users new to the command line, Track C:

- `skills/hi/playbook/canon/terminal-survival-kit.md`
- `skills/hi/playbook/canon/tmux-for-long-runs.md`
- `skills/hi/playbook/canon/git-the-bare-minimum.md`
- `skills/hi/playbook/canon/claude-code-daily-habits.md`
- `skills/hi/playbook/canon/asking-well.md`
