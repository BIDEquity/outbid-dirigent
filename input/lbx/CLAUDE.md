## Tool Usage
- Never pipe git commands (e.g. `git show ... | sed`). Use the dedicated Read tool with `offset`/`limit` parameters instead to view specific line ranges.
- Please execute `source /app/bin/scripts.sh` for every bash to be able to use integrated aliases and functions on cli level properly
  - if on host level, please use `source bin/scripts.sh` and try to execute tools by first going to docker level using `mp-open-php`

## ClickUp task resolution (shared convention for skills)

When a skill needs a ClickUp task ID, follow this order:

1. **Explicit argument** — use the task ID from the invocation if provided (pattern: `DV-\d+`, case-insensitive).
2. **Working branch** — extract from the current branch name (e.g. `task/DV-1234/...`).
3. **Ask the user** — if neither yields a task ID, ask with `AskUserQuestion`.

When fetching task context, always use both `mcp__clickup__get_task` and `mcp__clickup__get_task_comments`. If either call fails (task not found, network error, etc.), inform the user and proceed without ClickUp context rather than stopping entirely.

## General
- We are using Symfony framework
- You are located in a docker container
- Before running any docker related commands call `mp-tenant dummy`. Use this if prompted. This is required only once.

## Skill Chaining

- After `/test-review`: When the review identifies missing tests (coverage gaps), additionally ask the user whether the tests should be generated directly via `/test-generate`.

## Best Practice

Please use the contents from `src/_Doc/best_practice` for reading best practice.
