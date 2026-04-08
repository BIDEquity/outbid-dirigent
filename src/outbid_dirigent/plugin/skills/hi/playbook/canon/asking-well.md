# Asking well

**Track:** Setup & habits

**Thesis:** The quality of the output is bounded by the quality of the ask. Not by the model. Not by the harness. By you. Good asks aren't magic — they're a small set of learnable habits.

## The five habits of a good ask

### 1. Say what you want, not what you don't want

- Bad: *"Don't make it complicated."*
- Good: *"Use a single file. No new dependencies. Under 100 lines."*

Negatives are ambiguous; positives are verifiable. Give the agent a target, not a prohibition.

### 2. Give it a concrete outcome to hit

- Bad: *"Make the login page better."*
- Good: *"After this change, submitting the login form with wrong credentials should show an inline error 'Invalid email or password' within 200ms, without a page reload."*

If you can write the acceptance test, write it. If you can't, you don't know what you want yet — go figure it out before asking.

### 3. Point at the code, don't describe it

- Bad: *"There's some function somewhere that handles auth…"*
- Good: *"Look at `src/auth/session.ts:handleLogin`. Modify it so that…"*

File paths, line numbers, function names. The more precise you are, the less the agent has to guess. Guessing is where mistakes happen.

### 4. State the constraints upfront

- Bad: *"Add dark mode."* (…agent writes 400 lines…) *"Wait, I meant just the toggle, not the whole theme system."*
- Good: *"Add a dark mode toggle. Just the toggle UI component and localStorage persistence. Do NOT refactor the existing theme system, we'll do that in a follow-up."*

Out-of-scope is a gift to both of you. The agent won't gold-plate, you won't spend the next hour rolling back.

### 5. Paste errors and logs in full

- Bad: *"It's failing with some permissions thing."*
- Good: *"When I run `dirigent --spec SPEC.md --repo .`, I get:*
  > ```
  > PermissionError: [Errno 13] Permission denied: '.dirigent/PLAN.json'
  > Traceback (most recent call last):
  >   File "cli.py", line 42, in main
  >     ...
  > ```
  *I've already tried `chmod -R u+w .dirigent/`."*

Full stack trace, what you've already tried, what the current state is. This saves three rounds of "can you show me the error?"

## The spec principle applies to chat too

[spec-first-or-suffer](spec-first-or-suffer.md) is about dirigent, but the same logic applies to plain Claude Code chat. The agent is executing on whatever version of your intent it parses from your message. If that version is wrong, the code is wrong — and fixing it mid-flow is more expensive than fixing it up front.

Before pressing Enter on a non-trivial ask, ask yourself:

1. **Do I know what "done" looks like?** If no, I'm asking too early.
2. **Have I told the agent what's out of scope?** If no, I'm inviting scope creep.
3. **Have I pointed at the code I want changed?** If no, I'm making the agent guess.
4. **Are the constraints explicit?** If no, I'll be correcting them later.

Thirty seconds of pre-ask discipline saves ten minutes of post-ask correction.

## When to chat vs when to dirigent

This is the question the coach helps you answer, but the heuristic is simple:

- **Chat (interactive Claude Code):** exploratory, feedback-loop-fast, "I need to see and react to each step," small-ish changes.
- **Dirigent:** bounded, testable, "I can write the acceptance criteria now," long-running, you want to do something else while it runs.

If you're not sure, start in chat. Once the scope is clear, write a SPEC and hand it to dirigent. Chat is where you *figure out*; dirigent is where you *execute*.

## The meta-habit

Every time an ask goes badly, spend 30 seconds asking *why*. Not "the model is dumb" — specifically: what was ambiguous in my ask? What constraint did I forget? What piece of context did I assume the agent had? Write it down once. Next time, don't repeat it.

That's the whole skill. A year of this and your asks will hit first-time 80% of the time, and you'll understand *why* the 20% didn't.
