[Skip to main content](https://docs.entire.io/cli/checkpoints#content-area)

[Entire home page![light logo](https://mintcdn.com/entire/dU84oUx3gFbNHZ8_/logo/light.svg?fit=max&auto=format&n=dU84oUx3gFbNHZ8_&q=85&s=6ce790665b11c249fbf9d14a33f846c4)![dark logo](https://mintcdn.com/entire/dU84oUx3gFbNHZ8_/logo/dark.svg?fit=max&auto=format&n=dU84oUx3gFbNHZ8_&q=85&s=4499c6eb37e0fdff05bed2f478dfe874)](https://docs.entire.io/)

Search...

Ctrl K

- [GitHub](https://github.com/entireio)
- [Discord](https://discord.gg/jZJs3Tue4S)

##### Getting Started

- [Introduction](https://docs.entire.io/introduction)
- [Quickstart](https://docs.entire.io/quickstart)
- [Core Concepts](https://docs.entire.io/core-concepts)

##### CLI

- [Installation](https://docs.entire.io/cli/installation)
- [Commands](https://docs.entire.io/cli/commands)
- [Configuration](https://docs.entire.io/cli/configuration)
- [Checkpoints](https://docs.entire.io/cli/checkpoints)
- [External Agent Plugins](https://docs.entire.io/cli/external-agents)

##### Entire.io

- [Overview](https://docs.entire.io/web/overview)
- [Dashboard](https://docs.entire.io/web/dashboard)
- [Repositories](https://docs.entire.io/web/repositories)
- [Checkpoints](https://docs.entire.io/web/checkpoints)
- [Sessions](https://docs.entire.io/web/sessions)

##### Integrations

- [Claude Code](https://docs.entire.io/integrations/claude-code)
- [Copilot CLI (preview)](https://docs.entire.io/integrations/copilot-cli)
- [Cursor](https://docs.entire.io/integrations/cursor)
- [Factory Droid (preview)](https://docs.entire.io/integrations/factory-droid)
- [Gemini CLI (preview)](https://docs.entire.io/integrations/gemini-cli)
- [OpenCode (preview)](https://docs.entire.io/integrations/opencode)

- [Get Started](https://entire.io/)

[Entire home page![light logo](https://mintcdn.com/entire/dU84oUx3gFbNHZ8_/logo/light.svg?fit=max&auto=format&n=dU84oUx3gFbNHZ8_&q=85&s=6ce790665b11c249fbf9d14a33f846c4)![dark logo](https://mintcdn.com/entire/dU84oUx3gFbNHZ8_/logo/dark.svg?fit=max&auto=format&n=dU84oUx3gFbNHZ8_&q=85&s=4499c6eb37e0fdff05bed2f478dfe874)](https://docs.entire.io/)

Search...

Ctrl KAsk AI

- [Get Started](https://entire.io/)
- [Get Started](https://entire.io/)

Search...

Navigation

CLI

Checkpoints

[Documentation](https://docs.entire.io/introduction)

[Documentation](https://docs.entire.io/introduction)

CLI

# Checkpoints

Copy page

How Entire captures your AI coding sessions

Copy page

Entire captures AI coding sessions as you work, and creates permanent checkpoints when you make Git commits.

## [​](https://docs.entire.io/cli/checkpoints\#how-it-works)  How It Works

1. Start an AI coding session (Claude Code, Gemini, OpenCode)
2. When you or the agent run `git commit`, the session data is attached to your commit
3. The checkpoint ID is added as a commit trailer. For example:

Report incorrect code

Copy

Ask AI

```
feat: Add user authentication

This commit adds OAuth2 login flow with Google and GitHub providers.

Entire-Checkpoint: a3b2c4d5e6f7
```

4. The session log and other metadata are stored in a checkpoint in the `entire/checkpoints/v1` branch
5. On your next `git push`, the `entire/checkpoints/v1` branch will be automatically pushed too

## [​](https://docs.entire.io/cli/checkpoints\#benefits)  Benefits

- **Clean Git history** \- No extra commits from Entire
- **Safe everywhere** \- Can be used on `main` or any branch
- **Rewind support** \- You can rewind file changes and session state
- **Resume support** \- You or a coworker can resume a branch / commit session

## [​](https://docs.entire.io/cli/checkpoints\#best-practices)  Best Practices

- Make commits at logical stopping points or ask your agent to make granular commits
- Use meaningful commit messages—they become checkpoint labels
- Commit before major changes if you want a rewind point

### [​](https://docs.entire.io/cli/checkpoints\#auto-summarize)  Auto-Summarize

When enabled, Entire uses AI to automatically generate summaries of your sessions when you commit. These summaries are stored with your checkpoint metadata.

Report incorrect code

Copy

Ask AI

```
{
  "strategy_options": {
    "summarize": {
      "enabled": true
    }
  }
}
```

Auto-summarize requires Claude CLI to be installed and authenticated. The
summary generation happens in the background and won’t block your commit.

Summaries include:

- A brief description of what was accomplished
- Key decisions made during the session
- Files that were modified

Was this page helpful?

YesNo

[Previous](https://docs.entire.io/cli/configuration) [External Agent PluginsBuild plugins that integrate third-party AI agents with the Entire CLI\\
\\
Next](https://docs.entire.io/cli/external-agents)

Ctrl+I

[x](https://x.com/entirehq) [github](https://github.com/entireio/cli)

On this page

- [How It Works](https://docs.entire.io/cli/checkpoints#how-it-works)
- [Benefits](https://docs.entire.io/cli/checkpoints#benefits)
- [Best Practices](https://docs.entire.io/cli/checkpoints#best-practices)
- [Auto-Summarize](https://docs.entire.io/cli/checkpoints#auto-summarize)

Assistant

Responses are generated using AI and may contain mistakes.