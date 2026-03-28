---
name: quick-scan
description: Quick scan of relevant files for a feature (Hybrid route)
---

# Quick Scan

Analyze the codebase to implement the feature described in `.dirigent/SPEC.md`.

## Step 1

Read `.dirigent/SPEC.md` to understand the feature.

## Step 2

Scan the repo for files relevant to this feature. Focus ONLY on the relevant parts — no full codebase analysis needed.

## Step 3

Write `.dirigent/CONTEXT.md`:

```markdown
# Relevant Files for Feature

## Main Files
(Files that must be directly modified)

## Dependencies
(Files that must be understood but not changed)

## Patterns
(Coding patterns used in the project)

## Integration Points
(Where the new feature fits in)
```

## Constraints

- Focus ONLY on feature-relevant parts
- Identify the minimal set of files that need to be understood
- Document existing patterns the new feature should follow
