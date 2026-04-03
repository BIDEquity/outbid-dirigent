---
name: task-review
description: Review all changes on the current branch compared to main
argument-hint: [taskID] [review focus]

---

## Argument parsing

The user may invoke this skill as `/task-review [taskID] [review focus]`.

- `taskID` is an optional ClickUp task ID matching the pattern `DV-\d+` (case-insensitive).
- Everything after the task ID (or from the start if no task ID is given) is the **review focus** — extra instructions to incorporate into the review.


## Review context

- Commit messages: !`git log main..HEAD --format="commit %H%nauthor: %an%ndate: %ad%n%n    %s%n%n%b%n---"`
- Branch diff (committed): !`git diff main...HEAD`
- Staged diff (uncommitted): !`git diff --cached`
- Git status: !`git status --short`
- Review datetime: !`date +"%Y%m%d-%H%M"`

## 1. Determine the task ID

Follow the shared **ClickUp task resolution** convention from CLAUDE.md (steps 1 and 2 only — if neither yields a task ID, proceed without ClickUp context instead of asking).

## 2. Guard: on main with no task

If the current branch is `main` **and** no task ID was resolved, output an error:

> "Error: You are on `main` and no task ID was provided. Please provide a task ID or switch to a feature branch."

Then stop.

## 3. When a task ID is resolved

1. **Fetch the ClickUp task** — follow the shared ClickUp convention from CLAUDE.md (including error handling). If ClickUp is unreachable, proceed with a plain diff review.
2. Incorporate the task requirements into your review — verify the implementation actually satisfies the task.

## 4. Perform the review

Perform a thorough code review of this branch.
Review not only the changed parts but also the affected domain logic — it should remain correct and consistent. Raise questions if you are unsure.

Focus on:
- Keeping domain logic correct
- Correctness and logic errors
- Potential bugs or edge cases
- Security concerns (e.g. injection, unvalidated input)
- Code quality and clean code principles
- Consistency with surrounding code patterns

If a **review focus** was provided, give it extra attention on top of the standard review points.

Structure the review in a way that:
- Start with a summary
- Review findings by severity High, medium, minor
- Provide structured feedback organized by file, with specific file and line references where applicable.
- Always write a verdict.

## 5. Results

If a task ID was resolved:
1. **Document results** inside `.claude-reviews/{taskID}/{datetime}_{status}.md`
   1. `mkdir -p .claude-reviews/{taskID}`
   2. `{status}` is either `approved` or `rejected`
   3. `git add {review file}` (no commit)
2. Output the results (md content) into the cli.
3. Ask the user using the `AskUserQuestion` tool whether they want to post the review as a comment on the ClickUp task.
4. **If the user selects Yes**, post the content of the review file as a comment on the ClickUp task (use `add_task_comment`).
