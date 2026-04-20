---
name: assess
description: Use when asked to 'assess this repo', 'check compliance', 'check maturity', 'review against engineering standards', 'audit this repo', or when the user wants to understand the current state of the repository against portfolio engineering standards.
---

Assess this repository against all portfolio engineering standards and produce a prioritized improvement roadmap.

## Instructions

### Step 1 — Check for an existing assessment

Check if `harness-docs/standards-status.md` exists in this repository.

**If it exists:**

1. Read `harness-docs/standards-status.md`.
2. Display the Summary table (MUST ✅ / MUST ❌ / REC ✅ / REC ❌ per section).
3. If `harness-docs/remediation-plan.md` exists, read it and display the "Skills to run" table from it. Otherwise, list the top failing MUST items grouped by section with the remediation skill for each group (see Remediation Map below).
4. Output:
   > Assessment last run on [assessed_at date from the HTML comment at the top of the file]. Run `/verify-assessment` to re-check after making changes.
5. Stop — do not re-scan the repository.

**If it does not exist**, proceed to Step 2.

---

### Step 2 — Full assessment via parallel subagents

Read `harness-docs/engineering-standards.md` from the repository root. Then spawn **10 parallel subagents** using the Agent tool — one per section. Pass each subagent:
- The full text of its assigned section from `harness-docs/engineering-standards.md`
- The instruction below

**Instruction for every subagent:**

> You are assessing this repository against one section of the engineering standards. Read the section text provided. Extract every MUST and RECOMMENDED requirement. For each requirement, scan the repository for concrete evidence of compliance. Return a markdown table with these columns: Requirement (brief, max 80 chars), Level (MUST or REC), Status, Notes. Status values: ✅ PASS (name the evidence file/pattern), ❌ FAIL (evidence absent), ⚠️ WARN (partially present — explain why), ➖ SKIP (not applicable). Do not guess. Ambiguous evidence → ⚠️ WARN with explanation.

**Section assignments:**

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

---

### Step 3 — Write `harness-docs/standards-status.md`

Aggregate all 10 subagent results. Write `harness-docs/standards-status.md` using the Write tool. Use today's date for all Verified values. Set Fixed By to `—` for all rows.

File format:

```
<!-- assessed_at: YYYY-MM-DD -->
<!-- assessed_by: /assess -->

# Standards Status

> Last assessed: **YYYY-MM-DD** via `/assess` · Run `/verify-assessment` to update.

## Summary

| Category | MUST ✅ | MUST ❌ | REC ✅ | REC ❌ |
|---|---|---|---|---|
| 01 · Culture & Working Agreements | X | Y | Z | W |
| 02 · Architecture & Decision Records | X | Y | Z | W |
| 03 · Code Quality, Reviews & Standards | X | Y | Z | W |
| 04 · Test Strategy | X | Y | Z | W |
| 05 · Continuous Delivery & CI/CD | X | Y | Z | W |
| 06 · Feature Toggles | X | Y | Z | W |
| 07 · Observability, Monitoring & Tracking | X | Y | Z | W |
| 08 · Security & Dependency Management | X | Y | Z | W |
| 09 · Incident Management & Blameless Culture | X | Y | Z | W |
| 10 · Agentic Development | X | Y | Z | W |
| **Total** | **X** | **Y** | **Z** | **W** |

---

## 01 · Culture & Working Agreements

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| ... | MUST | ✅ PASS | YYYY-MM-DD | — | ... |

---

## 02 · Architecture & Decision Records

| Requirement | Level | Status | Verified | Fixed By | Notes |
|---|---|---|---|---|---|
| ... | MUST | ❌ FAIL | YYYY-MM-DD | — | ... |

---

(repeat for all 10 sections)
```

---

### Step 4 — Display summary, write remediation plan, and display it

After writing the status file, print the Summary table and list failing MUST items with the relevant skill using the Remediation Map below.

Then write `harness-docs/remediation-plan.md` using the Write tool. Populate it as follows:

- Set `generated_at` to today's date and `generated_by` to `/assess`
- **Skills to run** table: group failing MUST rows by skill (from the Remediation Map), deduplicate, order by section number, collapse multiple requirements onto one row in the "Failing requirements addressed" column (separated by ` · `)
- **Full failing MUST inventory**: one row per failing MUST item across all 10 sections, with its section, requirement text, and suggested skill
- If no MUST items are failing, replace both tables with: `> No failing MUST items — all MUST requirements are passing.`

File format:

```
<!-- generated_at: YYYY-MM-DD -->
<!-- generated_by: /assess -->

# Remediation Plan

> Generated **YYYY-MM-DD** · Run `/verify-assessment` to refresh after making changes.

## Skills to run

| Priority | Skill | Failing requirements addressed |
|---|---|---|
| 1 | `/add-ci` | CI pipeline missing or incomplete · Release automation absent |
| 2 | `/test-bootstrap` | Unit or integration tests absent |

## Full failing MUST inventory

| Section | Requirement | Suggested skill |
|---|---|---|
| 05 · Continuous Delivery & CI/CD | CI pipeline missing or incomplete | `/add-ci` |
```

**Remediation map:**

| Failing area | Suggested skill |
|---|---|
| Working Agreement / DoD / Retrospectives | `/working-agreement` |
| ADRs missing or not stored in `/harness-docs/adr/` | `/adr` |
| README incomplete or missing | `/document-codebase` |
| Tech debt not catalogued | `/tech-debt` |
| Unit or integration tests absent | `/test-bootstrap` |
| Test coverage gaps | `/test-coverage` |
| CI pipeline missing or incomplete | `/add-ci` |
| Release automation / Conventional Commits missing | `/add-release` |
| PIR process missing | `/pir` |
| Feature toggles absent or ad-hoc | `/add-feature-toggle` |
| Ad-hoc toggle patterns or stale flags found | `/feature-toggle-audit` |
| Structured logging absent or not JSON | `/add-structured-logging` |
| Tracking plan missing | `/tracking-plan` |
| CVE / dependency scanning absent | `/add-security-scan` |
| OWASP / secrets / IAM audit needed | `/security-audit` |
| Section 10 / Agentic standards absent | `/setup-agentic-standards` |
| CLAUDE.md stale or missing agentic block | `/audit-claude-md` |

End with:
> Assessment written to `harness-docs/standards-status.md`. Remediation plan written to `harness-docs/remediation-plan.md`. Commit both to track progress over time. Run `/verify-assessment` after making changes.
