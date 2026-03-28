---
name: create-contract
description: Create acceptance criteria contract for a phase before execution begins
---

# Create Phase Contract

## Step 1: Read Phase Details

Read `.dirigent/PLAN.json` and find the phase matching the provided phase ID. Understand all its tasks, their descriptions, and files they'll change.

Also read `.dirigent/SPEC.md` for the feature context.

## Step 2: Create the Contract

Write `.dirigent/contracts/phase-{PHASE_ID}-CONTRACT.md`:

```markdown
# Phase {PHASE_ID} Contract: {PHASE_NAME}

## Objective
{One sentence: what this phase achieves}

## Acceptance Criteria

1. **[AC-{PHASE_ID}-01]** {Specific, measurable criterion}
   - Verification: {How to verify}
2. **[AC-{PHASE_ID}-02]** {Specific, measurable criterion}
   - Verification: {How to verify}

## Quality Gates

- [ ] All new/modified files compile without errors
- [ ] No regressions in existing functionality
- [ ] Code follows project conventions
- [ ] All CRITICAL review findings from previous iterations resolved

## Out of Scope for This Phase

- {What this phase does NOT cover}

## Files Expected to Change

- `path/to/file` — {what changes}
```

## Rules

1. Each criterion MUST be specific and measurable (not "code is clean")
2. Each criterion MUST have a verification method
3. Maximum 8 acceptance criteria per phase
4. Derive criteria from the task descriptions
5. Include both functional and quality criteria
6. If `outbid-test-manifest.yaml` exists, reference its commands as verification methods
