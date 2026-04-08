# Read before you write

**Track:** Agent rule (enforced in `implement-task`, `fix-review`)

**Thesis:** Do not propose edits to code you haven't read. Grep + Read is cheaper than a revert, every time, without exception.

## The failure mode

The agent "knows" roughly what a file should contain and writes edits based on that mental model. Half the time it's right. The other half, the file doesn't look like the agent imagined: a helper it "knows" exists was renamed last month, an import path changed, a wrapper was added, a type was narrowed. The edit lands anyway because the replacement looks plausible — and then nothing works and the real file is now broken.

The debugging cost of this is large and *asymmetric*: writing from imagination takes seconds, but tracing a revert takes minutes, and explaining to a human reviewer why the edit "looked right" takes the rest of the afternoon.

## The rule

- **Never edit a file you have not read in this session.** Not "read once last week." Not "read a similar file." *This* file, *this* session, before the edit.
- **Never reference a function, class, or symbol you have not confirmed exists.** Grep for it. If grep comes back empty, your mental model is wrong — stop and investigate.
- **Never assume import paths.** Read the imports at the top of the consumer file. Read the file being imported. Confirm.
- **Never assume a type signature.** If you're calling a function, read its definition first.

## Why this keeps being tempting

Reading feels slow. Typing feels productive. That's an illusion: the time spent reading is time not spent in a revert loop. The "fast" path that skips reading is almost always slower end-to-end, and it produces code the user can't trust.

## How to apply

- Before any Edit: Read the file. Full. Not a snippet.
- Before any call to a function you didn't write in this session: confirm the signature.
- Before any "I'll just move this to a helper": grep for existing helpers first. They usually exist.
- If you catch yourself saying "I think this file has…", you haven't read it yet. Read it.

## Enforced in

- `skills/implement-task/SKILL.md` — engineering standards: "You are the long-term maintainer. Every line you write, you will read again in 6 months." (Canon strengthens this to explicit read-before-edit.)
- `skills/fix-review/SKILL.md` — Fixes must be minimal and focused; impossible to do safely without reading the surrounding code first.
