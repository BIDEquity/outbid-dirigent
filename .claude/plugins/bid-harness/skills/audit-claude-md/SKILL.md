---
name: audit-claude-md
description: Use when asked to 'audit CLAUDE.md', 'check agent instructions', 'is our CLAUDE.md stale', or on a quarterly cadence per the engineering standard.
---

Audit CLAUDE.md for staleness, dead instructions, and scope violations.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 10 · Agentic Development` to understand which CLAUDE.md hygiene items are currently failing.

## Instructions

1. **Read `CLAUDE.md`** in full. If it does not exist, output:
   > CLAUDE.md not found. Run `/setup-agentic-standards` first to create one.
   Then stop.

2. **Check for staleness signals** — references to things that no longer exist in the repo:
   - File paths mentioned in instructions: check each path exists with the Read tool
   - Tool or library names: cross-check against `package.json`, `go.mod`, `pyproject.toml`, or `pom.xml`
   - Stack references (e.g. "this is a Python service") that no longer match the detected stack
   - Commands referenced that no longer exist in the repo's scripts, Makefile, or `package.json`

3. **Check for dead instructions** — rules that no longer apply:
   - References to features, endpoints, or modules that have been deleted from the codebase
   - Instructions about a CI provider that is no longer in use (e.g. CircleCI config deleted but CLAUDE.md still references it)
   - Rules about a testing framework that has been replaced

4. **Check for scope violations** — instructions encoding things not enforced in this repo's CI:
   - Organisation-wide policies stated as repo facts but with no corresponding CI gate in this repo
   - Instructions about external systems (Jira board names, Slack channels, Notion pages) that could become stale without any signal
   - Cross-team conventions that belong in a shared document, not a repo-scoped CLAUDE.md

5. **Check for missing Section 10 coverage:**
   - Is there an "Agentic Development" section? If not, recommend running `/setup-agentic-standards`.
   - If present: does it define an autonomy level? Does it list blast-radius actions? Does it mention prompt injection?

6. **Produce a findings report in the conversation** (do not write a file — this is a review, not a document):

   ```
   ## CLAUDE.md Audit — YYYY-MM-DD

   ### Staleness findings (N)
   - Line 14: References `src/auth/legacy.ts` — file does not exist
   - Line 31: Mentions `jest` as test framework — project now uses `vitest`

   ### Dead instructions (N)
   - Lines 44–48: Rule about `feature/payments-v2` branch — branch deleted 6 months ago

   ### Scope violations (N)
   - Line 22: "Follow the Jira board at acme.atlassian.net/PAYMENTS" — external reference with no CI enforcement

   ### Missing Section 10 coverage
   - No autonomy level defined — run /setup-agentic-standards

   ### Clean (categories with 0 findings)
   - (none)
   ```

7. **For each finding, propose a specific edit.** Show the current line and the proposed replacement. Ask for approval before making any change. Apply all approved changes in a single edit pass after collecting all approvals.

## Update the status file

After completing the audit (and applying any approved changes), update `harness-docs/standards-status.md`:

1. Find the section heading `## 10 · Agentic Development`.
2. For each row below, update Verified to today's date, Fixed By to `/audit-claude-md`, and update Status and Notes:
   - Row matching "Treat CLAUDE.md as a first-class artifact": Status → `✅ PASS` if CLAUDE.md exists and is committed to git.
   - Row matching "Remove instructions that no longer apply": Status → `✅ PASS` if no dead instructions found (or all were removed in this session).
   - Row matching "Scope agent instructions to the repository they live in": Status → `✅ PASS` if no scope violations found.
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `10 · Agentic Development` row.
