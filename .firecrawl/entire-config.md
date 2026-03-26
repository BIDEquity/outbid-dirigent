[Skip to main content](https://docs.entire.io/cli/configuration#content-area)

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

Configuration

[Documentation](https://docs.entire.io/introduction)

[Documentation](https://docs.entire.io/introduction)

CLI

# Configuration

Copy page

Configure Entire settings for your project and preferences

Copy page

Entire uses a layered configuration system that allows project-wide settings to be shared via Git while supporting personal overrides.Entire looks for configuration in the following locations (in order of precedence):

1. **Local settings** (highest priority): `.entire/settings.local.json`
2. **Project settings**: `.entire/settings.json`
3. **Defaults** (lowest priority)

## [​](https://docs.entire.io/cli/configuration\#project-settings)  Project Settings

Project settings are stored in `.entire/settings.json` and should be committed to your repository. These settings apply to everyone working on the project.

Report incorrect code

Copy

Ask AI

```
{
  "enabled": true,
  "log_level": "info",
  "telemetry": true,
  "strategy_options": {}
}
```

### [​](https://docs.entire.io/cli/configuration\#settings-reference)  Settings Reference

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | `true` | Whether Entire is active in this repository |
| `log_level` | string | `"info"` | Log verbosity: `debug`, `info`, `warn`, `error`. Can be overridden by `ENTIRE_LOG_LEVEL` env var. |
| `telemetry` | boolean | `null` | Send anonymous usage analytics. `null` = not asked yet (will prompt), `true` = opted in, `false` = opted out |
| `strategy_options` | object | `{}` | Additional configuration options (see [Checkpoints](https://docs.entire.io/cli/checkpoints#strategy-options)) |

## [​](https://docs.entire.io/cli/configuration\#local-settings)  Local Settings

Local settings are stored in `.entire/settings.local.json` and are automatically added to `.gitignore`. Use these for personal preferences that shouldn’t be shared.

Report incorrect code

Copy

Ask AI

```
{
  "log_level": "debug",
  "telemetry": false
}
```

Local settings are merged with project settings. You only need to specify the
settings you want to override.

## [​](https://docs.entire.io/cli/configuration\#global-settings)  Global Settings

Global settings apply to all repositories and are stored in `~/.config/entire/settings.json`.

Report incorrect code

Copy

Ask AI

```
{
  "telemetry": true
}
```

### [​](https://docs.entire.io/cli/configuration\#global-settings-reference)  Global Settings Reference

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `telemetry` | boolean | `false` | Default telemetry setting for new repositories |

## [​](https://docs.entire.io/cli/configuration\#environment-variables)  Environment Variables

Certain settings can be overridden via environment variables:

| Variable | Description |
| --- | --- |
| `ENTIRE_ENABLED` | Set to `false` to disable Entire globally |
| `ENTIRE_LOG_LEVEL` | Set log verbosity |
| `ENTIRE_TELEMETRY` | Enable/disable telemetry |

Report incorrect code

Copy

Ask AI

```
# Enable debug logging for a session
ENTIRE_LOG_LEVEL=debug claude
```

## [​](https://docs.entire.io/cli/configuration\#agent-hook-configuration)  Agent Hook Configuration

Each agent stores its hook configuration in its own directory. When you run `entire enable`, hooks are installed in the appropriate location for each selected agent:

| Agent | Hook Location | Format |
| --- | --- | --- |
| Claude Code | `.claude/settings.json` | JSON hooks config |
| Gemini CLI | `.gemini/settings.json` | JSON hooks config |
| OpenCode | `.opencode/plugins/entire.ts` | TypeScript plugin |
| Factory Droid | `.factory/settings.json` | JSON hooks config |

You can enable multiple agents at the same time — each agent’s hooks are independent.

## [​](https://docs.entire.io/cli/configuration\#initializing-configuration)  Initializing Configuration

When you run `entire enable`, a `.entire` directory is created with default settings:

Report incorrect code

Copy

Ask AI

```
.entire/
├── settings.json        # Project settings (committed)
├── settings.local.json  # Local overrides (gitignored)
└── .gitignore          # Ensures local settings aren't committed
```

## [​](https://docs.entire.io/cli/configuration\#modifying-settings)  Modifying Settings

### [​](https://docs.entire.io/cli/configuration\#via-cli)  Via CLI

Report incorrect code

Copy

Ask AI

```
# Enable telemetry
entire enable --telemetry
```

### [​](https://docs.entire.io/cli/configuration\#manually)  Manually

Edit the JSON files directly:

Report incorrect code

Copy

Ask AI

```
# Edit project settings
vim .entire/settings.json

# Edit local settings
vim .entire/settings.local.json
```

## [​](https://docs.entire.io/cli/configuration\#configuration-precedence-example)  Configuration Precedence Example

Given these configuration files:**Global** (`~/.config/entire/settings.json`):

Report incorrect code

Copy

Ask AI

```
{
  "telemetry": true
}
```

**Project** (`.entire/settings.json`):

Report incorrect code

Copy

Ask AI

```
{
  "log_level": "info"
}
```

**Local** (`.entire/settings.local.json`):

Report incorrect code

Copy

Ask AI

```
{
  "log_level": "debug"
}
```

The effective configuration would be:

Report incorrect code

Copy

Ask AI

```
{
  "log_level": "debug",         // from local (overrides project)
  "telemetry": true             // from global
}
```

## [​](https://docs.entire.io/cli/configuration\#viewing-current-configuration)  Viewing Current Configuration

To see the effective configuration:

Report incorrect code

Copy

Ask AI

```
entire status --detailed
```

This shows all settings and their sources.

Was this page helpful?

YesNo

[Previous](https://docs.entire.io/cli/commands) [CheckpointsHow Entire captures your AI coding sessions\\
\\
Next](https://docs.entire.io/cli/checkpoints)

Ctrl+I

[x](https://x.com/entirehq) [github](https://github.com/entireio/cli)

On this page

- [Project Settings](https://docs.entire.io/cli/configuration#project-settings)
- [Settings Reference](https://docs.entire.io/cli/configuration#settings-reference)
- [Local Settings](https://docs.entire.io/cli/configuration#local-settings)
- [Global Settings](https://docs.entire.io/cli/configuration#global-settings)
- [Global Settings Reference](https://docs.entire.io/cli/configuration#global-settings-reference)
- [Environment Variables](https://docs.entire.io/cli/configuration#environment-variables)
- [Agent Hook Configuration](https://docs.entire.io/cli/configuration#agent-hook-configuration)
- [Initializing Configuration](https://docs.entire.io/cli/configuration#initializing-configuration)
- [Modifying Settings](https://docs.entire.io/cli/configuration#modifying-settings)
- [Via CLI](https://docs.entire.io/cli/configuration#via-cli)
- [Manually](https://docs.entire.io/cli/configuration#manually)
- [Configuration Precedence Example](https://docs.entire.io/cli/configuration#configuration-precedence-example)
- [Viewing Current Configuration](https://docs.entire.io/cli/configuration#viewing-current-configuration)

Assistant

Responses are generated using AI and may contain mistakes.