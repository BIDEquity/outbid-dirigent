---
name: create-plugin
description: Scan this codebase and build a tailored .claude/ plugin — CLAUDE.md, skills, and agents specific to this project's actual stack and workflow
argument-hint: [output-dir]
---

# Create Plugin

Scan the current codebase and produce a complete plugin configuration that makes Claude Code maximally effective for THIS specific project.

**Output directory:** `$ARGUMENTS` (defaults to `.claude` if no argument given).

Parse the output directory: if `$ARGUMENTS` is empty or not provided, use `.claude`. Otherwise use the first argument as the target directory.

**This is NOT a generic plugin.** The output encodes the project's actual commands, test patterns, service setup, auth mechanism, and conventions — so Claude Code can develop on this codebase without asking how things work.

## Step 1: Map the Codebase

Use an Explore subagent to produce a deep operational analysis of the repository.

Prompt for the agent:

> Analyze this repository and produce an operational map. I need to understand:
>
> 1. Stack & services (languages, frameworks, databases, how services start)
> 2. Dev workflow (install, run, test, lint — exact commands)
> 3. Test infrastructure (frameworks, directories, fixtures, CI pipeline)
> 4. Auth & access (mechanism, test credentials, roles)
> 5. Existing AI/plugin config (.claude/, CLAUDE.md, conventions)
> 6. Key patterns & gotchas (naming, imports, error handling, non-obvious things)
>
> Be precise — include exact commands. Run discovery commands to verify. Return a comprehensive markdown report.

After the agent returns, keep its output in context — you will pass it directly to Step 3.

## Step 2: Check for Existing Config

Before generating, check what already exists in the output directory:
- Read `{output-dir}/CLAUDE.md` if it exists — preserve user customizations
- Read `{output-dir}/skills/` if it exists — don't duplicate existing skills
- Read `CLAUDE.md` at repo root if it exists

Note what to preserve, what to update, and what to create fresh.

## Step 3: Build the Plugin

Use a general-purpose subagent to create the plugin configuration.

Prompt for the agent (include the full codebase map from Step 1 inline):

> Build a plugin configuration at `{output-dir}/` for this project based on the operational map below.
>
> {paste the full codebase map from Step 1}
>
> **Output directory: {output-dir}** — write ALL files under this directory.
>
> Existing config to preserve:
> {list what you found in Step 2, or "None — fresh setup"}
>
> Create:
> 1. `{output-dir}/CLAUDE.md` — project instructions (under 100 lines): stack, key commands, conventions, gotchas
> 2. `{output-dir}/skills/run-tests/SKILL.md` — how to run tests in THIS project (exact commands, flags, test file patterns)
> 3. `{output-dir}/skills/dev-server/SKILL.md` — how to start the dev environment (if applicable)
> 4. `{output-dir}/skills/e2e-verify/SKILL.md` — how to verify features end-to-end (if applicable)
> 5. `{output-dir}/agents/test-writer.md` — test specialist tuned to THIS project's test patterns (if the project has tests)
>
> Every command must be verified — run it before writing it into a skill. Do NOT write generic skills that could apply to any project.

After the agent returns, verify the output:
- Read `{output-dir}/CLAUDE.md` and confirm it reflects the actual stack
- List `{output-dir}/skills/` and confirm skills were created
- Run one of the test commands from `run-tests` to confirm it works

## Step 4: Report

Tell the user what was created:
- List every file in `{output-dir}/` with a one-line description
- Show the test command from `run-tests` and whether it passed
- Note any ambiguities from the codebase map that need manual resolution

## Rules

- Do NOT overwrite existing `{output-dir}/CLAUDE.md` without preserving user content (merge, don't replace)
- Do NOT create generic skills — every skill must reference actual project commands
- If the project has `.opencode/` skills, mention them in the report as candidates for porting
- If the codebase map found ambiguities (e.g. multiple test runners, unclear auth), list them for the user to resolve
