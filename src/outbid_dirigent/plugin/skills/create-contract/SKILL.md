---
name: create-contract
description: Create acceptance criteria contract for a phase before execution begins
---

<role>Du erstellst formale Acceptance Criteria Contracts fuer Phasen. Jedes Kriterium muss spezifisch und messbar sein.</role>

<instructions>
<step id="1">Read `.dirigent/PLAN.json` and find the phase matching the provided phase ID. Understand all its tasks, descriptions, and files they change.</step>
<step id="2">Read `.dirigent/SPEC.md` for the feature context.</step>
<step id="3">If `outbid-test-manifest.yaml` exists, read it for available test commands to use as verification methods.</step>
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
      "verification": "How to verify (e.g. run command, check file exists, grep for pattern)",
      "category": "functional"
    },
    {
      "id": "AC-01-02",
      "description": "Another criterion",
      "verification": "How to verify",
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
<rule>Each criterion MUST have a concrete verification method — a command to run, a file to check, a pattern to grep</rule>
<rule>Maximum 8 acceptance criteria per phase</rule>
<rule>Derive criteria from the task descriptions in the phase</rule>
<rule>Include both functional criteria (category "functional") and quality criteria (category "quality")</rule>
<rule>If test manifest commands exist, reference them as verification methods</rule>
<rule>The "id" field MUST follow the pattern AC-{PHASE_ID}-{NN} (e.g. AC-01-01, AC-01-02)</rule>
<rule>The output MUST be valid JSON matching the schema exactly</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>The file path MUST be .dirigent/contracts/phase-{PHASE_ID}.json</constraint>
</constraints>
