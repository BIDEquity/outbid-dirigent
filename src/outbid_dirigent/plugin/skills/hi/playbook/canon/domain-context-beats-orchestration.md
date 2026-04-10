# Domain context beats orchestration

**Thesis:** A smaller agent with domain-specific skills will out-perform a bigger orchestrator without them. Invest in project-specific skills early. General-purpose intelligence is not a substitute for knowing the house style.

## The lesson

A smaller architect running inside a different harness — loaded with project-specific skills like `ruby-code-writing`, `form-builder`, and domain conventions — produced better output, faster, on a real migration than a bigger, more "orchestrated" setup without those skills.

This was not about model size. The smaller setup had *context the big one lacked*: it knew how this codebase writes forms, where validations belong, which patterns are sacred, which are legacy. The orchestrator was smarter in the abstract but dumber about the thing that mattered.

## Why this keeps being true

Every codebase is its own language. Not the programming language — the *dialect*: naming, layering, error handling, testing style, the ten small decisions that distinguish this repo from the textbook. A general-purpose agent can guess these. A skill-equipped agent *knows* them. Guesses are expensive because every wrong guess becomes a review comment or a revert.

## How to apply

- **When you land in a new codebase, spend the first hour writing skills, not code.** A `conventions` skill that documents "forms use X, validations go in Y, services are thin" pays for itself within a day.
- **Skills beat CLAUDE.md for discoverable patterns.** CLAUDE.md is a wall of text the model skims. A named skill is something it explicitly loads and follows.
- **Per-repo skills are fine, even encouraged.** `/my-repo:write-ruby-form` is not over-engineering — it's the house style made executable.
- **Don't rely on the model to figure out your stack.** Give it the stack directly. The time you save inferring conventions is less than the time you lose correcting its guesses.
- **If you catch dirigent producing "generic" code that doesn't match your repo, that's a skill you haven't written yet.** Write it. Add it to the convention skills block. The next task will feel different.

## The corollary for Dirigent

Dirigent is orchestration. Orchestration without domain context produces orchestrated mediocrity. Feed the executor skills that match your codebase and the same harness becomes dramatically better at the same task.
