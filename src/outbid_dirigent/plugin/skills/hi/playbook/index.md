# Playbook Index

The coach reads this file to decide when to inline a canon file during a session. Each entry: title, one-line hook, and a "surface when" trigger.

## Track A — Human playbook (how to vibecode well)

- **[spec-first-or-suffer](canon/spec-first-or-suffer.md)** — The SPEC is the cheapest place to fight scope battles.
  - *Surface when:* user tries to skip SPEC generation, or catches themselves saying "also, wait…" mid-execution.

- **[ultrathink-as-a-ritual](canon/ultrathink-as-a-ritual.md)** — `ultrathink` is a scalpel, not a hammer.
  - *Surface when:* user is at an architecture fork or sizing an unknown, or conversely over-using ultrathink on trivial tasks.

- **[when-not-to-use-dirigent](canon/when-not-to-use-dirigent.md)** — Match the tool to the task shape.
  - *Surface when:* user invokes dirigent for a 1-line tweak, exploratory spike, or "I don't know what I want yet" moment.

- **[domain-context-beats-orchestration](canon/domain-context-beats-orchestration.md)** — Project-specific skills beat bigger models.
  - *Surface when:* user complains that dirigent is producing "generic" code that doesn't match their codebase, or is starting in a new repo with no convention skills.

- **[atomic-commits-per-task](canon/atomic-commits-per-task.md)** — Each task is a commit. Protect that.
  - *Surface when:* user asks about squashing history, bundling tasks, or can't decide how to split a SPEC.

## Track B — Agent rules (how the agent behaves)

- **[scope-is-sacred](canon/scope-is-sacred.md)** — No features beyond the task.
  - *Surface when:* user asks why the agent didn't also fix a nearby thing, or is confused about deviation logs.

- **[verify-don't-vibe](canon/verify-dont-vibe.md)** — Structural checks are not optional.
  - *Surface when:* user asks how dirigent verifies work, or is running in an environment where the app can't boot.

- **[read-before-you-write](canon/read-before-you-write.md)** — Grep + Read beats a revert.
  - *Surface when:* user is reviewing a revert or a PR where the agent clearly edited blind.

- **[no-sycophancy-rule](canon/no-sycophancy-rule.md)** — Disagreement is the only way to stop compounding error.
  - *Surface when:* user notices the agent agreeing too readily, or is frustrated by "you are absolutely right."

- **[scratch-state-hygiene](canon/scratch-state-hygiene.md)** — Workspace is not deliverable.
  - *Surface when:* user finds `.dirigent/` or `.planning/` in a PR, or is setting up a new repo for dirigent.

## Track C — Setup & habits (for people new to the command line)

This track is for users who want to vibecode with dirigent but haven't spent years living in a terminal. Read these in order the first time; after that, they're reference.

- **[terminal-survival-kit](canon/terminal-survival-kit.md)** — Ten shell commands and a few habits are all you actually need.
  - *Surface when:* user asks basic shell questions, is confused by `cd`/`ls`/`pwd`, or says they've never used the terminal seriously before.

- **[tmux-for-long-runs](canon/tmux-for-long-runs.md)** — Keep dirigent alive when your laptop sleeps. Six key bindings, done.
  - *Surface when:* user asks about long-running jobs, complains about losing progress when their terminal closes, or is running dirigent on a remote machine.

- **[git-the-bare-minimum](canon/git-the-bare-minimum.md)** — Eight happy-path commands, seven "oh no" commands, and the GitHub CLI.
  - *Surface when:* user asks how to undo something in git, is confused by branches, or is opening their first PR.

- **[claude-code-daily-habits](canon/claude-code-daily-habits.md)** — Slash commands, permission modes, session hygiene, escape hatches.
  - *Surface when:* user asks about `/plan` vs `/clear`, doesn't know the permission modes, or has a conversation that's clearly suffering from context bleed.

- **[asking-well](canon/asking-well.md)** — Prompt discipline for chat and for dirigent SPECs. The quality of the output is bounded by the quality of the ask.
  - *Surface when:* user is getting bad results from vague asks, or asks "how do I get better at this?"

## Surfacing rules

1. **Never push unprompted during routine operation.** Only surface canon at explicit decision points (see triggers above) or when the user asks.
2. **Quote the thesis, link the file.** Don't inline the whole canon unless the user asks for it. One-sentence hook + path is enough.
3. **Respect the 2-min read promise.** If the file is longer than that, summarize and link.
4. **Track when canon has already been surfaced this session.** Don't repeat the same canon file twice in one conversation unless explicitly requested.
