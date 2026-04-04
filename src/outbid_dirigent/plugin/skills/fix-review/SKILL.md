---
name: fix-review
description: Fix issues found during phase review (executor role)
context: fork
agent: implementer
---

<role>Du bist der EXECUTOR. Der Reviewer hat Findings in `${DIRIGENT_RUN_DIR}/reviews/phase-{PHASE_ID}.json` dokumentiert. Deine Aufgabe: alle critical und warn Findings fixen.</role>

<instructions>
<step id="1">Read `${DIRIGENT_RUN_DIR}/reviews/phase-{PHASE_ID}.json` to get the structured review with findings.</step>
<step id="2">Read `${DIRIGENT_RUN_DIR}/contracts/phase-{PHASE_ID}.json` to understand which acceptance criteria failed.</step>
<step id="3">Fix all findings with severity "critical" first, then "warn". Skip "info" unless trivial.</step>
<step id="4">For each failed acceptance criterion (verdict "fail" in criteria_results), address the root cause noted in the "notes" field.</step>
<step id="5">Commit: `git add -A && git commit -m "fix(phase-{PHASE_ID}): review fixes iteration {N}"`</step>
</instructions>

<rules>
<rule>Fix findings in priority order: critical first, then warn</rule>
<rule>Each fix must be minimal and focused — do not change more than needed</rule>
<rule>No new features — only fix what the reviewer found</rule>
<rule>If no critical or warn findings exist, do nothing</rule>
<rule>Reference the ac_id when fixing a criterion-related issue</rule>
</rules>

<constraints>
<constraint>Keine neuen Features einfuehren — nur Fixes</constraint>
<constraint>Jeder Fix muss direkt auf ein Finding oder failed Criterion zurueckfuehrbar sein</constraint>
</constraints>
