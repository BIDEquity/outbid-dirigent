---
name: pir
description: Use when asked to 'create a PIR', 'document this incident', 'write a post-incident review', 'do a blameless postmortem', or after a production incident to capture learnings and action items.
---

Create a new Post-Incident Review (PIR) document.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 09 · Incident Management & Blameless Culture` to understand which incident management items are currently failing.

## Instructions

1. Ask the user for:
   - Incident title and date
   - Severity level (P1, P2, or P3)
   - Timeline of key events (detection, investigation, mitigation, resolution)
   - Root cause (blameless — focus on systems and processes, not individuals)
   - What went well during the response
   - What could be improved
   - Action items with owners and due dates

2. Create the PIR file at `harness-docs/pir/YYYY-MM-DD-<slug>.md` using the template
   at `harness-docs/templates/pir-template.md`. Use the incident date for the filename.

3. If the `harness-harness-docs/pir/` directory doesn't exist, create it.

4. Set the review date to today. Remind the user that P1/P2 PIRs must be
   completed within 48 hours of the incident.

5. Remind the user to schedule the PIR action items in the next sprint.

## Update the status file

After creating the PIR file, update `harness-docs/standards-status.md`:

1. Find the section heading `## 09 · Incident Management & Blameless Culture`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/pir`, Notes to the PIR filename created:
   - Row matching "Conduct post-incident reviews (PIRs) within 48 hours of any P1 or P2 incident"
   - Row matching "Treat PIR action items as first-class work" (if action items with owners were recorded)
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `09 · Incident Management & Blameless Culture` row.
