# Terminal survival kit

**Track:** Setup & habits (for people new to the command line)

**Thesis:** You don't need to become a terminal wizard. You need maybe ten commands, a terminal app that doesn't fight you, and the habit of reading what's on screen before pressing Enter.

## The minimum viable setup

- **A good terminal app.** On macOS: iTerm2 or Warp (Warp is friendlier for beginners; iTerm2 is more configurable). On Windows: Windows Terminal + WSL2. On Linux: whatever ships is fine.
- **A sensible font.** Anything with ligatures and a clear distinction between `O` and `0`, `l` and `1`. JetBrains Mono, Fira Code, or Berkeley Mono all work.
- **Shell integration for copy/paste of multi-line prompts.** Most terminals mangle long pasted prompts. Warp handles this out of the box; iTerm2 needs "Paste as single line" disabled.

## The ten commands you actually need

| Command | What it does | Example |
|---|---|---|
| `pwd` | Where am I? | `pwd` → `/Users/you/projects/myapp` |
| `ls` | What's in this directory? | `ls -la` (the `-la` shows hidden files and details) |
| `cd` | Move to another directory | `cd ~/projects/myapp` |
| `cat` | Print a file to the screen | `cat README.md` |
| `less` | Read a file page by page (press `q` to quit) | `less long-log.txt` |
| `grep` | Find text in a file | `grep "error" log.txt` |
| `find` | Find files by name | `find . -name "*.py"` |
| `open .` | Open the current directory in Finder (macOS) | `open .` |
| `history` | What did I run earlier? | `history \| tail -20` |
| `clear` | Clear the screen | `clear` (or Cmd+K in most terminals) |

That's it. You don't need more to survive. You'll pick up `sed`, `awk`, `xargs`, and friends as you go — but only if you genuinely need them, not because a blog post said you should.

## Habits that save you from yourself

- **Read what's on screen before pressing Enter.** The terminal tells you exactly what it's about to do. Most disasters happen when people type-and-confirm on autopilot.
- **Don't paste commands you don't understand.** If you can't explain what `rm -rf /` does, you shouldn't run it. Ask the agent to explain first.
- **Use tab-completion aggressively.** Start typing a filename, press Tab. If it completes, you spelled it right. If it doesn't, you didn't.
- **Use `Ctrl+R` to search command history.** Faster than retyping.
- **When in doubt, `pwd` first.** Half of "it didn't work" is "you were in the wrong directory."

## Red flags — stop and think

If a command you're about to run contains any of these, pause:

- `rm -rf` — especially with a variable or wildcard
- `sudo` — you're about to run something as admin
- `> file` — you're about to *overwrite* that file (use `>>` to append instead)
- `git push --force` — you're about to overwrite remote history
- Anything piped into `sh` or `bash` from the internet — you're running code you haven't read

If the agent suggests any of these and you're not sure, ask *why* before running.

## Next: [tmux-for-long-runs.md](tmux-for-long-runs.md)

Once you're comfortable with the terminal, the next upgrade is keeping sessions alive when your laptop sleeps. That's what tmux is for.
