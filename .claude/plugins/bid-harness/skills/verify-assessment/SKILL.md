---
name: verify-assessment
description: Use when asked to 'verify the assessment', 'update the standards status', 're-check compliance', 'refresh the assessment', or when engineers have made manual changes and want to reconcile harness-docs/standards-status.md with the current state of the repository.
---

Re-run the full standards assessment, show what changed since the last run, and update `harness-docs/standards-status.md`.

## Instructions

### Step 1 — Read the existing assessment

Read `harness-docs/standards-status.md`.

If it does not exist, output:
> No existing assessment found. Run `/assess` first to create one.

Then stop.

Capture the current Status value for every row as the **before** snapshot.
Note the `assessed_at` date from the HTML comment at the top of the file.

---

### Step 2 — Re-run all section subagents

Read `harness-docs/engineering-standards.md` from the repository. Spawn **10 parallel subagents** using the Agent tool — one per section, with the same assignments as `/assess`:

| Subagent | Section |
|---|---|
| 1 | 01 · Culture & Working Agreements |
| 2 | 02 · Architecture & Decision Records |
| 3 | 03 · Code Quality, Reviews & Standards |
| 4 | 04 · Test Strategy |
| 5 | 05 · Continuous Delivery & CI/CD |
| 6 | 06 · Feature Toggles |
| 7 | 07 · Observability, Monitoring & Tracking |
| 8 | 08 · Security & Dependency Management |
| 9 | 09 · Incident Management & Blameless Culture |
| 10 | 10 · Agentic Development |

Use the same subagent instruction as `/assess`:

> You are assessing this repository against one section of the engineering standards. Read the section text provided. Extract every MUST and RECOMMENDED requirement. For each requirement, scan the repository for concrete evidence of compliance. Return a markdown table with these columns: Requirement (brief, max 80 chars), Level (MUST or REC), Status, Notes. Status values: ✅ PASS (name the evidence file/pattern), ❌ FAIL (evidence absent), ⚠️ WARN (partially present — explain why), ➖ SKIP (not applicable). Do not guess. Ambiguous evidence → ⚠️ WARN with explanation.

---

### Step 3 — Compute and display the diff

Compare the before snapshot (existing file) with the after snapshot (subagent results).
Match rows by Requirement text.

Print only changed items:

```
## What changed since [assessed_at date]

✅ Now passing (N)
  [Section] — [Requirement]
  ...

❌ Now failing (N)
  [Section] — [Requirement]
  ...

⚠️ Status changed (N)
  [Section] — [Requirement]: [old] → [new]
  ...

No change: N items
```

If nothing changed, print:
> No changes detected since [assessed_at date]. The repository state matches the last assessment.

---

### Step 4 — Overwrite `harness-docs/standards-status.md`

Write the updated file using the same format as `/assess`, with:
- `assessed_at` updated to today's date
- `assessed_by` set to `/verify-assessment`
- For rows that previously had a non-`—` Fixed By value and are still ✅ PASS: preserve the Fixed By value
- For rows that newly became ✅ PASS with no prior Fixed By: set Fixed By to `manual`
- Recalculate all summary totals

Print the new summary totals after writing.

---

### Step 5 — Display remediation suggestions and write remediation plan

After updating all rows, scan the failing MUST rows across all sections and print a remediation suggestion table for any failing item that maps to a skill using the Remediation Map below.

Then overwrite `harness-docs/remediation-plan.md` using the Write tool. Use the same format as `/assess`:

- Set `generated_at` to today's date and `generated_by` to `/verify-assessment`
- **Skills to run** table: group failing MUST rows by skill, deduplicate, order by section number, collapse multiple requirements onto one row
- **Full failing MUST inventory**: one row per failing MUST item
- If no MUST items are failing, replace both tables with: `> No failing MUST items — all MUST requirements are passing.`

**Remediation map:**

| Failing area | Suggested skill |
|---|---|
| Working agreements absent | `/working-agreement` |
| ADR process absent | `/adr` |
| Codebase undocumented | `/document-codebase` |
| Tech debt not catalogued | `/tech-debt` |
| No test strategy | `/test-bootstrap` |
| Test coverage gaps | `/test-coverage` |
| CI pipeline absent | `/add-ci` |
| Release automation absent | `/add-release` |
| PIR process missing | `/pir` |
| Feature toggles absent or ad-hoc | `/add-feature-toggle` |
| Ad-hoc toggle patterns or stale flags found | `/feature-toggle-audit` |
| Structured logging absent or not JSON | `/add-structured-logging` |
| Tracking plan missing | `/tracking-plan` |
| CVE / dependency scanning absent | `/add-security-scan` |
| OWASP / secrets / IAM audit needed | `/security-audit` |
| Section 10 / Agentic standards absent | `/setup-agentic-standards` |
| CLAUDE.md stale or missing agentic block | `/audit-claude-md` |

Only print rows where the corresponding area is still failing. If no MUST items are failing, skip the printed table.
