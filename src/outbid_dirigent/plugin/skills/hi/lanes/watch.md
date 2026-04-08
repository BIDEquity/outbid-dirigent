# Lane 1 — Watch it work

**Goal:** In under 60 seconds, show the user a real dirigent planning pass on the bundled sample repo, narrated step by step, with zero risk to their own code. Then optionally execute the plan for real inside a git worktree.

## The sample payload

The repo ships with `example/sample-repo/` which already contains a valid SPEC at `example/sample-repo/.dirigent/SPEC.md` (greeting + math utilities). It is the canonical onboarding demo.

## Script

### Step 1 — Narrate the setup

> "I'm going to run dirigent's planner against a tiny sample repo that ships with the plugin. It defines two trivial utility modules — `greet` and `calc`. This is 100% read-only. Your repo stays untouched."

### Step 2 — Invoke `dirigent:create-plan` directly

Instead of shelling out to the full `dirigent` CLI (which would set up a complete run directory and execute tasks), invoke the `dirigent:create-plan` skill with the sample repo as the target. This produces a real `PLAN.json` in the sample repo's `.dirigent/` directory without executing any tasks.

The key insight: `create-plan` is already a standalone skill. Reuse it. Don't build a parallel planner just for onboarding.

If `dirigent:create-plan` cannot be invoked against an arbitrary repo path from the current session, fall back to running `dirigent --spec example/sample-repo/.dirigent/SPEC.md --repo example/sample-repo --plan-only` (if that flag exists) or `dirigent ... --dry-run` — check the CLI capabilities at runtime. If neither works, abort this lane gracefully and suggest Lane 2 instead.

### Step 3 — Render the plan via `/dirigent:show-plan`

Invoke the existing `/dirigent:show-plan` slash command against the sample repo's PLAN.json. This is the same output the user would see in a production run — don't reinvent the rendering.

### Step 4 — Narrate what the user is seeing

Read the rendered plan and explain it in human terms:

> "Here's what dirigent did. It auto-detected this as a **Greenfield** route because there's no existing test infrastructure. It split the SPEC into N phases and M tasks. Each task you see here would, in a real run, spawn a fresh Claude Code process with its own context window. Each task commits atomically. The reviewer checks each phase against a contract before the next one starts. If a task fails, dirigent can resume from exactly there — no lost work."
>
> "That's the whole loop: SPEC → PLAN → task → commit → review → next task → ship."

Adjust the numbers to match what the planner actually produced. Do not hardcode phase/task counts.

### Step 5 — Offer execution

Ask (via AskUserQuestion):

> "Want to actually run it? I'll spin up a git worktree so your real repo stays untouched, execute the plan against the sample, and show you the resulting commits and PR-ready branch. Or we can stop here — you've seen the shape."

Options:
- **Yes, execute in a worktree** — invoke `superpowers:using-git-worktrees` to create an isolated worktree of `example/sample-repo`, then run `dirigent --spec .dirigent/SPEC.md --repo .` inside it. When done, show `git log --oneline` and the final state.
- **No, I've seen enough** — thank them, offer lanes 2, 3, or 4 as next steps.

### Step 6 — Debrief

After execution (or skip), surface one canon file if the user expresses curiosity:
- "How does it know when to split into phases?" → `atomic-commits-per-task.md`
- "What if the SPEC is wrong?" → `spec-first-or-suffer.md`
- "Would this work on a real legacy codebase?" → `domain-context-beats-orchestration.md`

Never surface more than one canon file automatically. Follow the surfacing rules in `playbook/index.md`.

## Safety rules

- **Never execute dirigent against the user's actual repo in this lane.** Only against the bundled sample, and only inside a worktree if they opt in.
- **Never delete `.dirigent/` from the sample repo.** Leave it as-is for the next user.
- **If a worktree is created, tell the user the path** so they can inspect it and clean up.
