[Skip to main content](https://docs.entire.io/core-concepts#content-area)

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

Getting Started

Core Concepts

[Documentation](https://docs.entire.io/introduction)

[Documentation](https://docs.entire.io/introduction)

Getting Started

# Core Concepts

Copy page

Understanding sessions, checkpoints, and branches

Copy page

## [​](https://docs.entire.io/core-concepts\#sessions)  Sessions

A **session** represents a complete interaction with an AI coding agent from start to finish. When you start Claude Code, or another supported agent, Entire automatically creates a new session.

### [​](https://docs.entire.io/core-concepts\#what%E2%80%99s-captured-in-a-session)  What’s Captured in a Session

- **Conversation transcript** \- The prompts you sent and responses from the AI
- **Code changes** \- All file modifications made during the session
- **Checkpoints** \- Save points you can rewind to
- **Token usage** \- Input/output tokens, cache usage, and API call counts
- **Metadata** \- Timestamps, agent type, and configuration
- **Line Attribution** \- A calculation of how many lines agents and humans contributed to the session

All sessions are stored locally in your project folder as well as on GitHub when you push. To find your raw session data on GitHub, check out the [Sessions Branch](https://docs.entire.io/core-concepts#sessions-branch) section below.

### [​](https://docs.entire.io/core-concepts\#nested-sessions)  Nested Sessions

When an AI agent spawns sub-agents (like Claude Code’s Task tool), Entire captures these as nested sessions within the parent session, preserving the full hierarchy of interactions.

## [​](https://docs.entire.io/core-concepts\#checkpoints)  Checkpoints

A **checkpoint** is a snapshot that you can rewind to—think of it as a “save point” in your work.Checkpoints have a 12-character hex ID, like: `8a513f56ed70`, You’ll find Checkpoint IDs in the web application as well as in the CLI.

### [​](https://docs.entire.io/core-concepts\#types-of-checkpoints)  Types of Checkpoints

Temporary Checkpoints

Created on **shadow branches** during active sessions. These contain the full state snapshot
with code and metadata, allowing you to rewind at any point during your session. Shadow branches
are named `entire/<sessionID>-<worktreeID>`, but remain local.

Committed Checkpoints

When you make a Git commit, the checkpoint metadata is stored permanently on the
`entire/checkpoints/v1` branch, which gets synced with your upstream. The checkpoint ID is added
to your commit message as a trailer:

Report incorrect code

Copy

Ask AI

```
Add user authentication

Entire-Checkpoint: a3b2c4d5e6f7
```

### [​](https://docs.entire.io/core-concepts\#when-checkpoints-are-created)  When Checkpoints Are Created

Checkpoints are created when you or the agent make a Git commit. Entire captures all session data during your work, and when you commit, the checkpoint metadata is permanently stored and linked to your commit.

## [​](https://docs.entire.io/core-concepts\#capture-strategy)  Capture Strategy

Entire captures all interactions in memory and on shadow branches as you work, but only creates permanent checkpoints when you or the agent make Git commits. This keeps your Git history clean while still providing full session capture.

- **No extra commits on your branch** — only your commits appear in history
- **Safe on any branch** — including `main`
- **Full rewind capability** — can still rewind during active sessions via shadow branches
- **Clean pull request history** — no noise from auto-generated commits

## [​](https://docs.entire.io/core-concepts\#branches)  Branches

Entire uses special Git branches to store session data without polluting your working branches.

### [​](https://docs.entire.io/core-concepts\#shadow-branches)  Shadow Branches

**Format:**`entire/<sessionID>-<worktreeID>`Shadow branches are temporary branches used to store checkpoints during active sessions. They enable the rewind feature by holding snapshots of your code at each checkpoint. The IDs are opaque.Shadow branches are automatically cleaned up and are not pushed to remote repositories.

### [​](https://docs.entire.io/core-concepts\#checkpoints-branch)  Checkpoints Branch

**Name:**`entire/checkpoints/v1`The checkpoints branch is a permanent branch that stores metadata for all completed sessions and checkpoints. This branch is pushed to your remote repository, allowing you to view sessions on [entire.io](https://entire.io/).

The checkpoints branch only contains metadata (JSON files), not your code. Your code remains on your normal branches.

## [​](https://docs.entire.io/core-concepts\#checkpoint-linking)  Checkpoint Linking

Entire links checkpoints to your commits using Git commit trailers:

Report incorrect code

Copy

Ask AI

```
feat: Add login form validation

Entire-Checkpoint: a3b2c4d5e6f7
```

This bidirectional linking allows:

- Finding the session context from any commit
- Using `entire explain` to understand how code was written
- Viewing session details in pull request reviews

### [​](https://docs.entire.io/core-concepts\#folder-structure-on-github)  Folder Structure on GitHub

The `entire/checkpoints/v1` branch contains all your checkpoint and session data, sharded by the first two characters of the checkpoint ID:

Report incorrect code

Copy

Ask AI

```
entire/checkpoints/v1 (branch)
├── 0b/                              # Shard (first 2 chars of checkpoint ID)
├── 0c/
├── 0f/
│   ├── 45ffa1b752/                  # Checkpoint (remaining chars)
│   ├── 4637ba1146/
│   └── f8ca6db1c9/                  # Full ID: 0ff8ca6db1c9
│       ├── metadata.json            # Checkpoint metadata
│       └── 0/                       # Session folder (numbered)
│           ├── content_hash.txt     # Hash of the content
│           ├── context.md           # Markdown of your prompts
│           ├── full.jsonl           # Full transcript with agent
│           ├── metadata.json        # Token usage, attribution, etc.
│           └── prompt.txt           # Raw prompts submitted
├── 10/
├── 11/
└── ...
```

### [​](https://docs.entire.io/core-concepts\#finding-your-session-data-on-github)  Finding Your Session Data on GitHub

1. Click on the branch dropdown in your project repo and select the `entire/checkpoints/v1` branch

![Screenshot of a checkpoint branch](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/checkpointsbranch.png?fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=bc6a238ad8b70063b26af1d63562b76b)

2. Then using either the search bar to the right of the branch dropdown or using CTRL+F, search for your checkpoint. It will highlight a folder for you to click on.

![Screenshot of a checkpoint search](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/cp-search.png?fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=5839148510341b65f3fb7797888fa893)

3. You will then see a `metadata.json` file which is the parent metadata file for all of your sessions. If you only have one session in that checkpoint then you will only see one folder:

![Checkpoint ](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/cp.png?fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=ddf39d080f1c24b7fc420397bc6edab0)

If you have multiple sessions, then you will see multiple folders.
4\. Click into a session folder to see your session files:

![Session files](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/sessions.png?fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=8a45f184fd2c3a39860e21377012ab65)

## [​](https://docs.entire.io/core-concepts\#token-usage-tracking)  Token Usage Tracking

Entire tracks token usage for each checkpoint:

- **Input tokens** \- Tokens sent to the AI
- **Output tokens** \- Tokens received from the AI
- **Cache creation** \- Tokens added to context cache
- **Cache reads** \- Tokens retrieved from cache
- **API calls** \- Number of API requests made

This helps you understand AI usage patterns and costs across your development.

## [​](https://docs.entire.io/core-concepts\#line-attribution)  Line Attribution

Entire tracks how much of a commit came from the agent vs you. When you commit code after working with an AI agent, the CLI calculates what percentage of the changes were agent-written vs human-written.This is captured in the `Entire-Attribution` trailer on commits:

Report incorrect code

Copy

Ask AI

```
feat: Add user authentication

Entire-Checkpoint: a3b2c4d5e6f7
Entire-Attribution: 73% agent (146/200 lines)
```

Attribution is calculated by tracking changes at two points:

1. **Before each agent run** — Entire captures what you changed since the last checkpoint
2. **At commit time** — Entire sums up all your edits and compares them to the agent’s contributions

A typical session looks like:

1. You write some code
2. Agent runs, adds more code (checkpoint created)
3. You edit the agent’s code and add your own
4. Agent runs again (another checkpoint)
5. You make final tweaks
6. You commit

Entire untangles these interleaved contributions to give you an accurate breakdown.

Was this page helpful?

YesNo

[Previous](https://docs.entire.io/quickstart) [InstallationInstall the Entire CLI on your system\\
\\
Next](https://docs.entire.io/cli/installation)

Ctrl+I

[x](https://x.com/entirehq) [github](https://github.com/entireio/cli)

On this page

- [Sessions](https://docs.entire.io/core-concepts#sessions)
- [What’s Captured in a Session](https://docs.entire.io/core-concepts#what%E2%80%99s-captured-in-a-session)
- [Nested Sessions](https://docs.entire.io/core-concepts#nested-sessions)
- [Checkpoints](https://docs.entire.io/core-concepts#checkpoints)
- [Types of Checkpoints](https://docs.entire.io/core-concepts#types-of-checkpoints)
- [When Checkpoints Are Created](https://docs.entire.io/core-concepts#when-checkpoints-are-created)
- [Capture Strategy](https://docs.entire.io/core-concepts#capture-strategy)
- [Branches](https://docs.entire.io/core-concepts#branches)
- [Shadow Branches](https://docs.entire.io/core-concepts#shadow-branches)
- [Checkpoints Branch](https://docs.entire.io/core-concepts#checkpoints-branch)
- [Checkpoint Linking](https://docs.entire.io/core-concepts#checkpoint-linking)
- [Folder Structure on GitHub](https://docs.entire.io/core-concepts#folder-structure-on-github)
- [Finding Your Session Data on GitHub](https://docs.entire.io/core-concepts#finding-your-session-data-on-github)
- [Token Usage Tracking](https://docs.entire.io/core-concepts#token-usage-tracking)
- [Line Attribution](https://docs.entire.io/core-concepts#line-attribution)

Assistant

Responses are generated using AI and may contain mistakes.

![Screenshot of a checkpoint branch](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/checkpointsbranch.png?w=840&fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=b2c6f4aba23b6d35c0f4d4b8dcdf74e8)

![Screenshot of a checkpoint search](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/cp-search.png?w=840&fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=5b2c95271cc72e84b1d3a78479f82c1d)

![Checkpoint ](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/cp.png?w=840&fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=7d9c39bb5229f8d851926e5fb3125735)

![Session files](https://mintcdn.com/entire/mT2JijRzz9bYcNhR/images/sessions.png?w=840&fit=max&auto=format&n=mT2JijRzz9bYcNhR&q=85&s=925c83ec9e635f1762df381399d24e74)