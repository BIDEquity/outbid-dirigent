---
name: create-contract
description: Create acceptance criteria contract for a phase before execution begins
---

<role>Du erstellst formale Acceptance Criteria Contracts fuer Phasen. Jedes Kriterium muss spezifisch, messbar und durch einen konkreten Befehl verifizierbar sein.</role>

<instructions>
<step id="1">Read `.dirigent/PLAN.json` and find the phase matching the provided phase ID. Understand all its tasks, descriptions, and files they change.</step>
<step id="2">Read `.dirigent/SPEC.md` for the feature context.</step>
<step id="3">If `.dirigent/test-harness.json` exists, read it. This is CRITICAL — the verification_commands and e2e_framework are the primary way the reviewer will verify criteria. Every functional criterion MUST reference an executable verification method.</step>
<step id="4">Create the contract JSON file at `.dirigent/contracts/phase-{PHASE_ID}.json` using the exact schema below.</step>
</instructions>

<output file=".dirigent/contracts/phase-{PHASE_ID}.json">
{
  "phase_id": "01",
  "phase_name": "Phase Name",
  "objective": "One sentence: what this phase achieves",
  "acceptance_criteria": [
    {
      "id": "AC-01-01",
      "description": "Specific, measurable criterion",
      "verification": "Run: curl -sf http://localhost:3000/api/health | jq .status",
      "category": "functional"
    },
    {
      "id": "AC-01-02",
      "description": "Another criterion",
      "verification": "Run: npx playwright test --grep 'feature name'",
      "category": "functional"
    },
    {
      "id": "AC-01-03",
      "description": "Code compiles without errors",
      "verification": "Run: npm run build (or equivalent)",
      "category": "quality"
    }
  ],
  "quality_gates": [
    "All new/modified files compile without errors",
    "No regressions in existing functionality",
    "Code follows project conventions"
  ],
  "out_of_scope": ["What this phase does NOT cover"],
  "expected_files": [
    {"path": "src/foo.py", "change": "Add new class"}
  ]
}
</output>

<rules>
<rule>Each criterion MUST be specific and measurable — not "code is clean" but "function X returns Y when given Z"</rule>
<rule>Each FUNCTIONAL criterion MUST have a verification method that starts with "Run: " followed by an executable command — the reviewer will execute this command and record its output as evidence</rule>
<rule>The reviewer CANNOT declare a criterion as "pass" without evidence from running the verification command — so make sure the command is actually runnable</rule>
<rule>Maximum 8 acceptance criteria per phase</rule>
<rule>Derive criteria from the task descriptions in the phase</rule>
<rule>Include both functional criteria (category "functional") and quality criteria (category "quality")</rule>
<rule>If test-harness.json has verification_commands, use them as verification methods (e.g. "Run: curl -sf http://localhost:3000/api/health" or "Run: npx playwright test")</rule>
<rule>If test-harness.json has e2e_framework.run_command, at least one criterion MUST use it as verification</rule>
<rule>If test-harness.json has an auth.login_command, criteria that test authenticated endpoints should reference it</rule>
<rule>Prefer e2e verification (HTTP requests, Playwright tests, CLI commands) over unit tests — unit tests alone do NOT prove the feature works end-to-end</rule>
<rule>The "id" field MUST follow the pattern AC-{PHASE_ID}-{NN} (e.g. AC-01-01, AC-01-02)</rule>
<rule>The output MUST be valid JSON matching the schema exactly</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>The file path MUST be .dirigent/contracts/phase-{PHASE_ID}.json</constraint>
<constraint>Do NOT create criteria that can only be verified by reading code — every criterion needs a runnable command</constraint>
</constraints>
