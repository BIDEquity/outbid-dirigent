# {Feature Name}

## Goal

{One paragraph. What is being built and why. Name the user problem this solves.}

## Requirements

- **R1** ({category}/{priority}): {Requirement text — concrete, single-claim, verifiable.}
- **R2** ({category}/{priority}): {Requirement text}

<!--
Format: `**Rn** (category/priority): text`

  Rn       sequential ID from R1, never reused, never renumbered.
  category one of: data-model, api, ui, auth, integration, infra, policy,
                   workflow, validation, testing, other
  priority one of: must, should, may

Rules:
- Split compound requirements ("X and Y and Z") into separate Rn entries.
- A requirement is verifiable if a reviewer can check it by running a command,
  inspecting a file, or observing a specific UI element/value. "Looks good" is
  not verifiable. "Body element has class `dark` when toggle is on" is.
-->

## Scope

### In Scope

- {What this feature includes}

### Out of Scope

- {What this feature explicitly does NOT include}

<!--
Out of Scope is required. If genuinely none, write exactly:
  - None — full scope is in scope.
Do not omit the section.
-->

## Technical Notes

{For each constraint the implementer must follow, name the file path, pattern,
or convention. Reference real files that exist in the repo. If no technical
notes apply, write `None`. If a needed input is missing, write
`TBD: <what you'd need>` so the planner sees the gap.}
