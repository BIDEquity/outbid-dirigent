# Atomic commits per task

**Thesis:** Dirigent commits per task, not per phase, not per PR. That's not a quirk — it's the single most useful property of the whole system. Structure your SPECs so each task *is* a commit, and everything downstream gets easier.

## Why it matters

Three things fall out of atomic per-task commits, all valuable, all hard to retrofit:

1. **Bisectability.** When something breaks three days later, `git bisect` points to the exact task that introduced it. Not the phase. Not the PR. The task, with its own name, summary, and deviation notes.
2. **Rollback surface.** If a task goes sideways, reverting it is a single commit. No surgical picking across a megacommit. No "let's keep this half but drop that half."
3. **Review sanity.** Reviewers (human or agent) see work in the same size-of-thought that wrote it. A 200-line task is reviewable. A 2000-line phase is not.

## Why it's worth protecting

The temptation is always to squash — "cleaner history," "fewer commits in the PR," "less noise." Every one of those is a false economy. The noise is the bisect resolution. Squashing trades a one-time aesthetic win for a permanent debugging penalty.

Dirigent's atomic commits are also what make *resumability* work. If task 5 fails, the state is precisely "tasks 1-4 committed, task 5 not." You resume from there. Without per-task commits, resume becomes ambiguous and the executor has to re-derive what's done.

## How to apply

- **Write SPECs so each requirement maps to one task that maps to one commit.** If you can't imagine the commit message, the task is probably too big.
- **Don't bundle "and also" into a task.** "Add auth endpoint" is a task. "Add auth endpoint and refactor the session store and update the migration" is three tasks.
- **Task descriptions become commit messages.** Write them like commit messages from day one: imperative mood, concrete outcome, no fluff.
- **Resist the urge to squash before merge.** If your team wants a single-commit PR, use a merge commit at the boundary and keep the atomic history below it.

The commit graph is documentation your future self will read. Treat it that way.
