# Ultrathink as a ritual

**Thesis:** `ultrathink` is a scalpel, not a hammer. Use it when the cost of a wrong turn is high and the path is unclear. Don't use it for code the model can write in its sleep.

## What it actually does

`ultrathink` (and its quieter cousin, "think harder") allocates more reasoning budget before the agent commits to an approach. It's the difference between *writing code* and *deciding what code to write*. The two are not the same activity, and only one of them benefits from more thinking.

## When it earns its keep

- **Architecture forks.** "Should this be a service or a module? Polling or webhook? Shared table or separate?" These are the expensive decisions. Paying for a minute of deliberation here saves hours of unwinding later.
- **Unfamiliar codebases.** When you don't know the conventions, the model doesn't either — but it *can* discover them if you give it room. "Ultrathink about how this codebase handles auth and match that pattern."
- **Sizing unknowns.** "Is this a 2-hour change or a 2-week change?" Better answered after 60 seconds of thinking than after 3 hours of writing.
- **Legacy debt.** "Ultrathink about the cheapest way to migrate this without breaking consumers." Thinking is much cheaper than bisecting a broken release.
- **Debugging ghosts.** When the bug doesn't match the code and you're about to guess — stop, ultrathink, form hypotheses from evidence.

## When it's wasted

- "Please write this CRUD endpoint." No fork, no ambiguity, no cost of being wrong. Just write it.
- Formatting, renaming, obvious refactors. The model already knows.
- Anywhere the next step is obvious. Thinking about obvious things doesn't make them more obvious.

## The ritual

Before any non-trivial planning moment, ask: *would I be mad if the agent picked the wrong option here?* If yes, `ultrathink`. If no, don't bother.

The discipline is binary: spend the budget where it matters, spend nothing where it doesn't.
