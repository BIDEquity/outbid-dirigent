# Git — the bare minimum

**Track:** Setup & habits

**Thesis:** You don't need to understand rebase, bisect, or reflog to vibecode with dirigent. You need about 8 commands and a very firm grasp of "how to undo." Dirigent handles the hard parts; you just need to not panic when things look weird.

## The 8 commands

| Command | What it does |
|---|---|
| `git status` | What's changed? What's staged? What branch am I on? Run this constantly. |
| `git diff` | What did I (or dirigent) actually change? Reads like a receipt. |
| `git log --oneline -10` | The last 10 commits, one line each. |
| `git add -A` | Stage everything. |
| `git commit -m "message"` | Commit with a message. (Dirigent does this for you, but you'll do it for non-dirigent work.) |
| `git checkout -b new-branch` | Create and switch to a new branch. |
| `git push -u origin branch-name` | Push a new branch to GitHub (first push only). Afterwards just `git push`. |
| `gh pr create` | Open a pull request from your current branch. Requires the GitHub CLI (`brew install gh`). |

That's the happy path. Most days, that's all you need.

## The "oh no" commands

Things will go sideways. Here's how to unstuck yourself without losing work:

| Situation | Command |
|---|---|
| "I want to throw away uncommitted changes in one file" | `git restore path/to/file` |
| "I want to throw away ALL uncommitted changes" (careful!) | `git restore .` |
| "I want to stash my changes temporarily" | `git stash` (later: `git stash pop` to get them back) |
| "I just committed something wrong" | `git reset --soft HEAD~1` (un-commits, keeps changes staged) |
| "I'm on the wrong branch with my changes" | `git stash` → `git checkout correct-branch` → `git stash pop` |
| "dirigent left some files I don't recognize" | `git status` first. Then `git clean -n` (dry run) → `git clean -f` (actually delete untracked files) |
| "I committed a secret 😱" | Rotate the secret immediately. Then ask the agent how to purge git history — and don't push until you have. |

## The habits that matter

- **`git status` before and after every dirigent run.** This is your safety net. If dirigent leaves files behind, you'll see them. If it committed something surprising, you'll see it.
- **Work on branches, not main.** `git checkout -b feature/thing` before you start anything non-trivial. This means when something goes sideways, `git checkout main` puts you back where you started.
- **Commit often, even outside dirigent.** Small commits are a form of insurance. A commit is a restore point.
- **Never `--force` push to main.** If you don't know what force-push means, you're not ready to do it, and that's fine.
- **Pull before you push.** `git pull --rebase` is usually safer than plain pull if you haven't committed yet.

## GitHub basics

Install `gh` once: `brew install gh && gh auth login`. Then:

```bash
gh pr create          # Open a PR from current branch
gh pr list            # List your open PRs
gh pr view 42         # See details of PR #42
gh pr checks          # Status of CI on the current PR's branch
gh pr merge 42        # Merge PR #42 (if you have permission)
gh issue list         # List issues
gh issue create       # Open a new issue
```

`gh` is dramatically less friction than the web UI. Install it once, thank yourself forever.

## When dirigent does git things

Dirigent commits per task (see `atomic-commits-per-task.md`). This means after a dirigent run you'll see a bunch of new commits on your current branch, each with a meaningful message. That's normal. That's the whole point.

What is NOT normal:
- Commits you didn't authorize on a branch you didn't expect.
- Force-pushes (dirigent should never force-push; if it does, that's a bug).
- Commits with scratch directories in them (see `scratch-state-hygiene.md`).

If you see any of these, stop, `git log`, and ask the agent to explain before doing anything else.

## Next: [claude-code-daily-habits.md](claude-code-daily-habits.md)
