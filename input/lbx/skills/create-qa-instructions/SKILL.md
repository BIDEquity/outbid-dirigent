---
name: create-qa-instructions
description: Generate QA test instructions from the current branch context and prepend them to the ClickUp task description
context: fork
agent: general-purpose
disable-model-invocation: true
---

## Determine the ClickUp task ID

Follow the shared **ClickUp task resolution** convention from CLAUDE.md.

## Instructions
1. **Fetch the ClickUp task** with description and comments — follow the shared ClickUp convention from CLAUDE.md (including error handling). If ClickUp is unreachable, you may still generate QA instructions from the diff alone but skip the "Present and update" ClickUp steps.
2. **Analyse the branch changes** against main:
   - !`git log main..HEAD --format="%s%n%b" --no-merges`
   - !`git diff main --name-only`
3. **Read changed files** as needed to understand what was done and what needs to be tested.

## Generate QA instructions

Write comprehensive QA test instructions following this structure:

```markdown
## QA Test Instructions — ({current date YYYY-MM-DD HH:MM})

### Context
Brief summary of what was changed and why — written for a QA tester who has no code context.

---

### 1. {Test scenario title}
- [ ] Step 1
- [ ] Step 2
- [ ] **Expected:** ...

### 2. {Next scenario}
...

### N. Regression — {area that could be affected}
- [ ] ...

---

### DEV — {developer-only verification title}
- [ ] ...
```

Guidelines:
- Each test scenario gets its own numbered section with a descriptive title.
- Steps are checkable bullet points (`- [ ]`).
- Expected results are **bold** and inline with the step.
- Include regression checks for areas affected by the change.
- Keep instructions concise but unambiguous — a QA tester should be able to follow them without reading the code.
- **DEV sections:** Points that require developer access (e.g. database queries, migration verification, log checks, config validation) must be flagged with a `DEV —` prefix in the section title and placed at the end, after all regular QA scenarios.

## Present and update

1. **Show the generated QA instructions** to the user in full.
2. **Ask the user** with `AskUserQuestion` whether to:
   - Prepend to the ClickUp task description as-is
   - Edit first (user provides feedback, you revise, then ask again)
3. **Once approved**, fetch the current task description via `mcp__clickup__get_task`, prepend the QA instructions block followed by a `---` separator, and update with `mcp__clickup__update_task_description`.
