# When NOT to use Dirigent

**Thesis:** Dirigent is for *bounded work you want to leave running*. Not for *figuring things out*. Match the tool to the shape of the task, not the other way around.

## Dirigent is wrong for

- **One-line tweaks.** If the change is "rename this function" or "update this constant", writing the SPEC takes longer than the change. Use plain Claude Code interactively.
- **Exploratory spikes.** "I don't know if this is even possible" — that's a research task, not an execution task. You need to be in the loop, poking at things. Dirigent assumes you already know what you want.
- **Figuring out what you want.** If you're still sketching requirements in your head, stop. Dirigent will happily implement your *current* thoughts, and you'll hate the result because those thoughts weren't right yet. Use interactive mode to think out loud first, *then* spec, *then* dirigent.
- **Debugging ghosts.** When you're tracing a flaky bug through 6 files, you need context in your head, not a headless agent. Dirigent doesn't do well at "poke until it stops misbehaving."
- **Anything where the feedback loop must be fast.** Dirigent commits a task, reviews it, maybe fixes, then commits the next one. If you need to see the result in 2 seconds and try another thing, that's not dirigent.

## Dirigent is right for

- **Features you can describe in a SPEC.** Scoped, testable, finite.
- **Legacy migrations.** Large, repetitive, rule-driven. Exactly where a headless loop shines.
- **Adding tracking / testability / scaffolding.** Boilerplate-heavy, easy to verify, boring to do by hand.
- **"I'll be at lunch, here's the spec."** Long-running, resumable, atomic commits. You come back, you review, you ship.

## The test

Before invoking dirigent, ask: *can I write the acceptance criteria right now, without thinking?* If yes, dirigent. If no, back to interactive mode until the answer becomes yes.

Using dirigent on the wrong task isn't a failure of dirigent. It's a failure of tool selection — and it's costly, because the feedback loop is slow enough that wasting one is expensive.
