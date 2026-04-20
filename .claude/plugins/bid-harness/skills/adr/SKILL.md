---
name: adr
description: Use when an architectural decision is being made, when asked to 'create an ADR', 'document this decision', 'write an architecture decision record', or when a significant technical choice needs to be recorded.
---

Create a new Architecture Decision Record (ADR).

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 02 · Architecture & Decision Records` to understand which ADR-related items are currently failing.

## Instructions

1. Ask the user for:
   - A short, descriptive title for the decision
   - The context — what problem or situation demands this decision?
   - The decision — what was decided?
   - The consequences — what are the trade-offs?
   - Alternatives considered — what other options were evaluated?

2. Determine the next ADR number by scanning existing files in `harness-docs/adr/`.
   If the directory doesn't exist, create it and start at 0001.

3. Create the ADR file at `harness-docs/adr/NNNN-<slug>.md` using the template
   at `harness-docs/templates/adr-template.md`. Generate the slug from the title
   (lowercase, hyphens, no special characters).

4. Set the status to "Proposed" and the date to today.

5. Remind the user to link the new ADR from the repository README.

6. If `ARCHITECTURE.md` exists at the repo root, remind the user that its
   "Architecture Decisions" section indexes ADRs by link — the new ADR
   should be added to that table. Suggest running `/generate-architecture --update`
   to refresh the index automatically. If `ARCHITECTURE.md` does not exist,
   skip this step (no-op).

## Update the status file

After creating the ADR file, update `harness-docs/standards-status.md`:

1. Find the section heading `## 02 · Architecture & Decision Records`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/adr`, and Notes to the ADR filename created:
   - Row matching "Document all significant architectural decisions as ADRs"
   - Row matching "Store ADRs in `/harness-docs/adr/`" (if this was the first ADR and the directory was just created)
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `02 · Architecture & Decision Records` row.
