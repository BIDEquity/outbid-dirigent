---
name: create-contract
description: Create acceptance criteria contract for a phase before execution begins
arguments: none - phase and plan context provided via prompt
---

# Create Phase Contract

Create a contract (acceptance criteria) that both the executor and reviewer agree upon before a phase begins.

## Purpose

The contract defines what "done" means for a phase. It is:
- Created BEFORE execution begins
- Used by the executor to know what to achieve
- Used by the reviewer to evaluate pass/fail
- The single source of truth for phase completion

## Output

Create `.dirigent/contracts/phase-{PHASE_ID}-CONTRACT.md`:

```markdown
# Phase {PHASE_ID} Contract: {PHASE_NAME}

## Objective
{One-sentence description of what this phase achieves}

## Acceptance Criteria

1. **[AC-{PHASE_ID}-01]** {Specific, measurable criterion}
   - Verification: {How to verify this criterion is met}
2. **[AC-{PHASE_ID}-02]** {Specific, measurable criterion}
   - Verification: {How to verify this criterion is met}
...

## Quality Gates

- [ ] All new/modified files compile without errors
- [ ] No regressions in existing functionality
- [ ] Code follows project conventions and patterns
- [ ] All CRITICAL review findings from previous iterations are resolved

## Out of Scope for This Phase

- {What this phase explicitly does NOT cover}

## Files Expected to Change

- `path/to/file.ext` — {what changes}
```

## Rules

1. Each criterion MUST be specific and measurable (not "code is clean")
2. Each criterion MUST have a verification method
3. Maximum 8 acceptance criteria per phase (keep it focused)
4. Criteria must be derived from the task descriptions in this phase
5. Include both functional criteria (what it does) and quality criteria (how well)
6. If test manifest commands exist, reference them as verification methods
