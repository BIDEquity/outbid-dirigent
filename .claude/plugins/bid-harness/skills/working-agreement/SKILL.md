---
name: working-agreement
description: Use when asked to 'create a working agreement', 'update the team working agreement', 'document team norms', 'set up team practices', or when a team wants to define how they collaborate.
---

Create or update a team Working Agreement.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 01 · Culture & Working Agreements` to understand which items are currently failing before scaffolding the document.

## Instructions

1. Check if a working agreement already exists (look for files named
   `working-agreement.md` or similar in `harness-docs/`).

2. If one exists, offer to review and update it. If not, create a new one.

3. Ask the user for:
   - Team name
   - Meeting cadences (standup, planning, retro, refinement)
   - Communication norms (primary channel, response expectations)
   - Definition of Done checklist
   - On-call expectations
   - Decision-making process
   - Code review norms

4. Use the template at `harness-docs/templates/working-agreement-template.md`
   to scaffold the document.

5. Save the working agreement to `harness-docs/working-agreement.md`.

6. Set "Last Reviewed" to today and "Next Review" to 3 months from today.

7. Remind the user that working agreements should be co-created by the team
   and reviewed quarterly.

## Update the status file

After saving the working agreement, update `harness-docs/standards-status.md`:

1. Find the section heading `## 01 · Culture & Working Agreements`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/working-agreement`, and Notes to a brief description of what was created:
   - Row matching "written Working Agreement" (or similar — covers cadences, DoD, on-call)
   - Row matching "Definition of Done" applied to every story
   - Row matching "retrospectives" (if the working agreement includes a retro cadence)
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `01 · Culture & Working Agreements` row.
