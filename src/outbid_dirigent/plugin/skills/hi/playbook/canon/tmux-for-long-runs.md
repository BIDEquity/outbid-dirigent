# tmux for long runs

**Track:** Setup & habits

**Thesis:** Dirigent runs can take 30+ minutes. You don't want to babysit a terminal window for 30 minutes, and you absolutely don't want your laptop going to sleep halfway through. tmux fixes both problems. Learn 6 key bindings and you're done forever.

## What tmux actually is

tmux is a "terminal multiplexer": a program that runs *inside* your terminal and keeps sessions alive even if you close the window, disconnect SSH, or your laptop sleeps. You start a long-running dirigent job in a tmux session, detach, close the terminal, come back tomorrow, and the job is either still running or long since finished — either way, the output is waiting for you.

It also splits one terminal into multiple panes, which is nice but secondary. The killer feature is *persistence*.

## Install

```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Verify
tmux -V
```

## The 6 key bindings you need

tmux commands are all triggered by a "prefix" key (default: `Ctrl+b`) followed by another key. So `Ctrl+b c` means "press Ctrl+b, release, then press c."

| Binding | Action |
|---|---|
| `tmux new -s dirigent` | Start a new session named "dirigent" |
| `Ctrl+b d` | **Detach** — leaves the session running, returns you to the normal shell |
| `tmux attach -t dirigent` | Re-attach to a session by name |
| `tmux ls` | List all running sessions |
| `Ctrl+b %` | Split pane vertically (side by side) |
| `Ctrl+b "` | Split pane horizontally (top/bottom) |
| `Ctrl+b arrow` | Move focus between panes |
| `Ctrl+b x` | Close current pane |

That's literally all you need. Six bindings, two shell commands.

## The dirigent workflow

```bash
# Morning: start a named session for the day's work
tmux new -s dirigent

# Inside tmux, run the long job
dirigent --spec .dirigent/SPEC.md --repo .

# Detach (laptop sleeps, you go to lunch, whatever)
# Ctrl+b d

# Later: reattach
tmux attach -t dirigent

# End of day: close cleanly by exiting the shell or killing the session
tmux kill-session -t dirigent
```

## Why this changes everything for vibecoding

Without tmux, long dirigent runs are fragile: a closed lid, a dropped WiFi, a terminal crash, and you've lost your progress and have to resume. With tmux, none of that matters. The job keeps running on the machine regardless of whether you're looking at it.

This is especially useful if you're running dirigent on a remote machine (EC2, a homelab box, a cloud dev env). SSH + tmux is the canonical "leave it running overnight" setup.

## A tmux config that's less hostile

The default prefix (`Ctrl+b`) is awkward. Most people rebind to `Ctrl+a`. Create `~/.tmux.conf`:

```
# Rebind prefix to Ctrl+a (closer to home row)
unbind C-b
set -g prefix C-a
bind C-a send-prefix

# Mouse support (click to switch panes, scroll history)
set -g mouse on

# Reasonable defaults
set -g history-limit 10000
set -g base-index 1
setw -g pane-base-index 1
```

Reload with `tmux source-file ~/.tmux.conf` inside a running session, or just start a new session.

## Alternatives

If tmux feels like too much, `screen` is older but simpler. Warp has built-in session persistence. iTerm2 has "Session restore." Any of these works. The important thing is *something persistent*, not specifically tmux.

## Next: [running-long-jobs.md](#) and the daily driver habits

You now have the hardware to run dirigent overnight. The software habits — when to kick things off, how to check progress without interrupting, when to just let it finish — are covered in the next canon file.
