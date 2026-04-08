# Spec first, or suffer

**Thesis:** The SPEC is the cheapest place to fight scope battles. Every battle you skip there, you pay for later — mid-execution, at 2x the cost, with half the context.

## The pattern

Across hundreds of sessions, the same shape repeats. You skip the spec. You tell the agent "just add dark mode." Twenty minutes in, you catch yourself typing: *"not done yet — monetization IS in scope actually."* Or: *"did you just declare that out of scope?"* Or: *"wait, I also wanted it to persist across sessions."*

Every one of those sentences is a spec battle that was deferred into execution. They cost more there:

- The agent has already made assumptions that now have to be unwound.
- Context is full of implementation detail that pushes out clarity.
- Correcting mid-flight feels adversarial — "you did it wrong" — when really, the spec never said.

## Why it keeps happening

The SPEC feels slow. It's a page of prose where you'd rather see code appear. So you skip it. But that's a cost illusion: the SPEC isn't slower than coding, it's slower than *imagining* coding. The actual work still has to happen. Front-loading the scope fight is nearly always cheaper than back-loading it.

## How to apply

- **Any feature bigger than 1 file:** spec it. Even a rough 10-line SPEC beats no SPEC.
- **Non-obvious scope boundaries:** write them down as *out of scope* explicitly. This is the line the executor won't cross.
- **Ambiguous requirements:** resolve them *now* with numbered, testable lines. "Users can toggle dark mode" is bad. "R1: dark mode toggle persists in localStorage across page reloads" is good.
- **Escape hatch:** if you genuinely can't scope something yet, that's not a spec problem — that's a *you don't know what you want yet* problem, and dirigent is the wrong tool. Use plain Claude Code interactively until you do.

If you catch yourself saying "actually, also…" during execution — stop, update the SPEC, and re-plan. Don't patch over it in chat.
