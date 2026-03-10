## Project Name
Outbid Dirigent

## One-Liner (1-2 sentences)
A headless Python control plane that takes a specification file, analyzes a target repository, chooses the optimal execution strategy, and autonomously implements the entire feature or migration using Claude Code — without any human interaction.

## The Problem
Implementing features or migrating legacy codebases requires a developer to sit in front of Claude Code, provide context, make decisions, and babysit the process. For large-scale migrations (e.g., Java to PHP), this can take days of manual guidance. On headless environments like Coder Workspaces, there's no interactive terminal at all — someone would need to SSH in and stay connected for hours. There was no way to just say "here's the spec, go build it" and walk away.

## The Solution
Dirigent acts as an autonomous orchestrator on top of Claude Code. It reads a SPEC.md, analyzes the target repo (language, history, complexity), picks the right execution route (Greenfield, Legacy, or Hybrid), extracts domain knowledge if needed, creates a phased execution plan, and then works through every task — one fresh Claude Code process per task, with atomic commits, automatic retries, and an AI Oracle for architecture decisions. Everything is resumable: if it crashes or times out, just run `--resume` and it picks up exactly where it left off.

## Key Features
- Automatic route selection (Greenfield / Legacy / Hybrid) based on repo analysis
- Proteus integration for deep domain extraction (fields, rules, events, dependencies)
- Phased execution plans with atomic commits per task
- AI Oracle for autonomous architecture decisions (no human needed)
- Full resumability via STATE.json — survives crashes, timeouts, and restarts
- Automatic branch creation, push, and PR via GitHub CLI
- Deviation detection and logging (bugs found, blockers resolved)
- Business rule guardrails for legacy migrations (no logic lost)
- Dry-run mode for safe analysis without changes
- Structured logging with timestamps for full audit trail

## Target Audience
- Outbid development team (internal tooling)
- Developers running autonomous coding tasks on Coder Workspaces
- Anyone who needs to execute large-scale code migrations or feature implementations without babysitting

## Use Cases

### Use Case 1: Legacy Migration on a Coder Workspace
A PortCo has a 4-year-old Java/Spring Boot application that needs to be migrated to PHP/Laravel. A developer writes a SPEC.md describing the migration, spins up a Coder Workspace with the source repo, and runs `dirigent --spec .planning/SPEC.md --repo . --use-proteus`. Dirigent analyzes the repo, selects the Legacy route, runs Proteus to extract 1200+ fields, 60+ business rules, and 30+ domain events, creates a phased migration plan, and autonomously implements it task by task. The developer checks back hours later to find a PR ready for review.

### Use Case 2: New Feature Implementation
A developer writes a SPEC.md for a new dashboard feature on an existing Next.js project. They run `dirigent --spec SPEC.md --repo .` and Dirigent selects the Greenfield route, creates a plan with 3 phases and 8 tasks, and implements everything with atomic commits. Each task gets its own Claude Code process with fresh context, preventing context window pollution.

### Use Case 3: Resuming After Interruption
A migration run times out after 2 hours during task execution. The developer runs `dirigent --spec SPEC.md --repo . --resume` and Dirigent loads the STATE.json, skips all completed steps (analysis, extraction, planning, and finished tasks), and continues from the exact task where it stopped.

## Integrations & Connections
- **Claude Code CLI**: Core execution engine — each task is a separate `claude` process invocation
- **Claude API (Anthropic)**: Used by the Oracle for autonomous architecture decisions
- **Proteus**: Deep domain extraction plugin for legacy codebases (fields, rules, events, dependencies)
- **GitHub CLI (`gh`)**: Automatic branch creation, push, and PR creation
- **Coder Workspaces**: Primary deployment target for headless execution

## Tech Stack
- **Frontend**: None (CLI tool)
- **Backend**: Python 3.8+
- **Database**: None (JSON files for state)
- **Hosting**: Runs locally or on Coder Workspaces
- **Other**: Claude Code CLI, Anthropic API, GitHub CLI

## What This Project Does NOT Do
- Not an IDE plugin or interactive coding assistant — it's fully headless
- Does not provide a web UI or dashboard
- Does not manage infrastructure or deployments
- Does not replace code review — it creates PRs for humans to review
- Does not support parallel task execution (tasks run sequentially by design)
- Does not work without Claude Code CLI installed

## Related Projects
- **proteus-alpha**: Domain knowledge extraction tool used by Dirigent's `--use-proteus` flag
- **outbid-platform**: The broader Outbid platform that Dirigent is part of

## Status
- [x] Live / Production

## Keywords & Tags
```
autonomous coding, headless agent, Claude Code, orchestrator, control plane,
code migration, legacy migration, business rule extraction, domain extraction,
Proteus, execution plan, atomic commits, resumable, Coder Workspaces,
greenfield, legacy, hybrid, routing engine, AI Oracle, SPEC.md,
task execution, autonomous development, code generation, refactoring
```

## Contact & Ownership
- **PortCo**: PMI (internal tooling)
- **Contact Person**: Josh
- **Created**: March 2026
- **Last Updated**: March 2026
