# Claude Code — daily habits

**Track:** Setup & habits

**Thesis:** Claude Code has maybe 15 commands and a handful of modes that actually matter day to day. Learn those, ignore the rest until you need them, and you'll spend zero time fighting the tool.

## The slash commands you'll use every day

| Command | What it does |
|---|---|
| `/clear` | Start a fresh conversation. Use whenever the agent seems "confused" by long context. |
| `/plan` | Enter plan mode — the agent reads and researches but won't touch files until you approve. Use for anything non-trivial. |
| `/status` | Shows current session info, permission mode, etc. |
| `/help` | Built-in reference. |
| `/dirigent:hi` | The coach — routes your intent to the right dirigent skill. |
| `/dirigent:show-plan` | Render the current dirigent PLAN.json. |
| `/dirigent:show-progress` | What phase/task is dirigent currently on? |
| `/commit` | If you have the commit skill installed, this creates a commit with an auto-generated message. |

Tab completion works on slash commands. Start typing `/dir` and you'll see every dirigent command.

## Permission modes — the thing that matters most

Claude Code runs in one of several modes. The difference is **who confirms destructive actions**:

- **Plan mode** — the agent can read files and run read-only commands, but cannot edit, write, or run destructive commands. Every proposed change needs your explicit approval. **Use for:** anything you're not sure about, first-time skill runs, anything on main.
- **Accept-edits mode (auto-approve)** — the agent can edit files freely but asks before running shell commands. **Use for:** implementing a plan you already trust.
- **Full auto mode** — the agent can edit and run commands freely. **Use for:** long-running dirigent jobs inside a git worktree (so any mistake is isolated).
- **Default** — asks for confirmation before each edit and each bash command. **Use for:** learning. Slow but safe.

The rule: **use the least permissive mode that isn't painful.** When you're new, that's Plan or Default. When you're comfortable, that's Accept-edits. Only go Full auto inside isolated worktrees.

## Writing prompts that work

The same principles from [spec-first-or-suffer](spec-first-or-suffer.md) apply to plain chat:

- **Be concrete.** "Add a health endpoint" is better than "make the app healthier."
- **Give it constraints.** "Don't touch anything outside `src/api/`." "Follow the existing pattern in `src/api/users.py`."
- **State what's out of scope.** "Do not add tests yet — I'll do that in a follow-up."
- **Paste errors in full.** Not a summary. Not "it fails with a permissions thing." The whole stack trace.
- **Say what you've already tried.** This stops the agent from redoing work you already ruled out.

Bad: *"Can you help me with auth?"*
Good: *"Add Google OAuth login to this Next.js app. Use NextAuth v5. Persist the session in the existing Postgres. Don't touch the existing password-based login, I'll remove it later. Start by reading `src/app/api/auth/route.ts` and the NextAuth v5 docs."*

## Session hygiene

- **Start a new session when the task changes.** Don't try to do "and now the next feature" in the same session — context bleeds badly.
- **Use `/clear` liberally.** It's free. A clean context is faster and more accurate than a long one.
- **When plan mode proposes something you don't understand, ask "why."** The agent will explain. Approving changes you don't understand is the single biggest source of regret.
- **If the agent keeps getting something wrong, stop.** Don't retry the same prompt louder. Switch to plan mode, make a smaller ask, or open a new session.

## The escape hatches

Things will get stuck. Here's how to unstick:

- **Agent is looping:** `Esc` to interrupt, then ask it to summarize what it's stuck on.
- **Agent is making stuff up:** switch to plan mode and force it to read files before proposing.
- **Context is too long:** `/clear` and start fresh. Paste only the essentials.
- **Agent is too agreeable:** remind it of `no-sycophancy-rule.md`. Or just push back yourself.

## Next: [asking-well.md](asking-well.md)

The final Track C file — how to write asks that work the first time, whether for dirigent or for plain chat.
