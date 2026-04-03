---
name: build-plugin
description: Scan a codebase and build a Claude Code plugin tailored to its stack, test setup, and dev workflow. Creates CLAUDE.md, skills, and agents specific to this project.
argument-hint: [output-dir]
disable-model-invocation: true
---

# Build Plugin

Scan the current codebase and produce a complete plugin configuration that makes Claude Code maximally effective for THIS specific project.

**Output directory:** `$ARGUMENTS` (defaults to `.claude` if no argument given).

Parse the output directory: if `$ARGUMENTS` is empty or not provided, use `.claude`. Otherwise use the first argument as the target directory.

**This is NOT a generic plugin.** The output encodes the project's actual commands, test patterns, service setup, auth mechanism, and conventions — so Claude Code can develop on this codebase without asking how things work.

## Step 1: Map the Codebase

Use the codebase-mapper agent (runs on Opus) to produce a deep operational analysis.

Prompt for the agent:

> Analyze this repository and produce an operational map. Write it to `.dirigent/codebase-map.md`.
>
> I need to understand:
> 1. Stack & services (languages, frameworks, databases, how services start)
> 2. Dev workflow (install, run, test, lint — exact commands)
> 3. Test infrastructure (frameworks, directories, fixtures, CI pipeline)
> 4. Auth & access (mechanism, test credentials, roles)
> 5. Existing AI/plugin config (.claude/, .opencode/, CLAUDE.md, conventions)
> 6. Key patterns & gotchas (naming, imports, error handling, non-obvious things)
>
> Be precise — include exact commands that work. Run discovery commands to verify. Your output drives a plugin generator.

After the agent returns, read `.dirigent/codebase-map.md`.

## Step 2: Check for Existing Config

Before generating, check what already exists in the output directory:
- Read `{output-dir}/CLAUDE.md` if it exists — preserve user customizations
- Read `{output-dir}/skills/` if it exists — don't duplicate existing skills
- Read `.opencode/` if it exists — consider porting useful skills to Claude format
- Read `CLAUDE.md` at repo root if it exists

Note what to preserve, what to port, and what to create fresh.

## Step 3: Build the Plugin

Use the plugin-writer agent to create the plugin configuration.

Prompt for the agent:

> Build a plugin configuration at `{output-dir}/` for this project based on the operational map below.
>
> {paste the contents of .dirigent/codebase-map.md}
>
> **Output directory: {output-dir}** — write ALL files under this directory.
>
> Existing config to preserve:
> {list what you found in Step 2, or "None — fresh setup"}
>
> Create:
> 1. `{output-dir}/CLAUDE.md` — project instructions (under 100 lines)
> 2. `{output-dir}/skills/run-tests/SKILL.md` — how to run tests in THIS project
> 3. `{output-dir}/skills/dev-server/SKILL.md` — how to start dev environment (if applicable)
> 4. `{output-dir}/skills/e2e-verify/SKILL.md` — how to verify features e2e (if applicable)
> 5. `{output-dir}/agents/test-writer.md` — test specialist for THIS project's patterns (if useful)
>
> Every command must be verified — run it before writing it into a skill. Don't write generic skills.

After the agent returns, verify the output:
- Read `{output-dir}/CLAUDE.md` and confirm it has the right stack info
- List `{output-dir}/skills/` and confirm skills were created
- Run one of the test commands from the skills to confirm it works

## Step 4: Report

Tell the user what was created:
- List every file in `{output-dir}/` with a one-line description
- Show the test command from `run-tests` and whether it passed
- Note any ambiguities from the codebase map that need manual resolution

## Rules

- Do NOT create anything yourself — delegate to codebase-mapper and plugin-writer agents
- Do NOT overwrite existing `{output-dir}/CLAUDE.md` without preserving user content (merge, don't replace)
- Do NOT create generic skills — every skill must reference actual project commands
- If the project has `.opencode/` skills, mention them in the report as candidates for porting
- If the codebase-mapper found ambiguities, list them for the user to resolve
