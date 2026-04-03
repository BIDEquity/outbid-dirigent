---
name: quick-feature
description: Implement a small feature end-to-end — plan, implement, review — using focused subagents. Use for changes that fit in 1-3 files.
disable-model-invocation: true
---

# Quick Feature

Implement a small feature end-to-end by orchestrating three subagents in sequence: plan, implement, review.

**Input:** $ARGUMENTS — a short description of what to build.

## Step 1: Plan

Use the infra-architect agent to analyze the codebase and produce a plan.

Prompt for the agent:

> Read the codebase structure. The user wants: "$ARGUMENTS"
>
> Write a brief plan to `.dirigent/quick-plan.md` with:
> - Which files to create or modify (be specific)
> - Which test files to create or modify (EVERY new feature MUST have tests)
> - What each change does (1-2 sentences per file)
> - How to verify it works (a command the reviewer can run — must include running the tests)
>
> The plan MUST include tests. No feature ships without tests.
> Keep it short — this is a small change, not a multi-phase project.

After the agent returns, read `.dirigent/quick-plan.md` to get the plan.

## Step 2: Implement

Use the implementer agent to execute the plan.

Prompt for the agent:

> Implement the following plan. Make atomic commits.
>
> {paste the contents of .dirigent/quick-plan.md}
>
> You MUST create tests for every new function and endpoint. Run ALL tests after your changes and ensure they pass. Write a summary to `.dirigent/summaries/quick-feature-SUMMARY.md`.

After the agent returns, verify the summary file exists.

## Step 3: Review

Use the reviewer agent to verify the implementation.

Prompt for the agent:

> Review the most recent commits against this plan:
>
> {paste the contents of .dirigent/quick-plan.md}
>
> Run the verification commands from the plan. Run the test suite. Check code quality. If tests are missing for new functionality, verdict MUST be "fail".
> Write your review to `.dirigent/reviews/quick-feature.json` using this exact schema:
>
> ```json
> {
>   "phase_id": "quick",
>   "iteration": 1,
>   "verdict": "pass",
>   "criteria_results": [
>     {"ac_id": "QF-01", "verdict": "pass", "notes": "...", "evidence": [{"command": "...", "exit_code": 0, "stdout_snippet": "..."}]}
>   ],
>   "findings": [],
>   "summary": "..."
> }
> ```

After the agent returns, read the review. If verdict is "pass", report success. If "fail", report the findings to the user.

## Rules

- Do NOT implement anything yourself — delegate ALL work to the subagents
- Do NOT skip the review step
- If the implementer fails, report the error — do not retry
- If the reviewer finds critical issues, report them — do not auto-fix
- Keep the plan scope small — if $ARGUMENTS describes a large feature, tell the user to use the full dirigent pipeline instead
