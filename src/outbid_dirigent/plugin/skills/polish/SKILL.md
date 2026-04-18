---
name: polish
description: Spec-to-code gap audit — read the spec, inspect the shipped code, find what the user asked for but can't actually do, fix the top-priority gaps. Replayable safety net after a build; also works on repos dirigent never touched.
context: fork
---

# Polish — Spec→Code Gap Audit

You are the last line of defense against silent drift. The build claims to match the spec. Your job is to **prove it or fix it from the user's perspective.** "The curl returns 200" is not proof; "the guest receptionist can scan a day ticket and see ADMIT on screen" is proof.

## When This Runs

- **After a dirigent run** — as a closing safety net. The plan, contracts, and reviewers all look upward from tasks; nothing looks downward from the spec.
- **On a repo dirigent never touched** — standalone replay mode. Stateless with respect to dirigent artifacts.

Both modes read the same inputs (SPEC + repo) and write the same outputs. There is no "dirigent-mode" / "standalone-mode" split in the skill logic.

## Inputs

1. **The spec**: `${DIRIGENT_RUN_DIR}/SPEC.md` (the run dir always has a copy, even in standalone mode)
2. **The compact spec** (if present): `${DIRIGENT_RUN_DIR}/SPEC.compact.json` — preferred. Organized `requirements[]` with `{id, category, priority, text}` plus `entities`, `flows`, `glossary`.
3. **The shipped code**: the target repo (current working directory)
4. **Scope hint from ARGUMENTS**: `--max-fixes N` (default 5), `--categories a,b,c` (restrict which req categories to audit)

If `SPEC.compact.json` is missing, proceed with raw `SPEC.md`. Do not block on regeneration — the compactor may fail without `ANTHROPIC_API_KEY` and polish must still be useful.

## Process

### Step 1 — Partition the audit into category chunks

Read the compact spec. Group requirements by `category` (data-model, api, ui, auth, workflow, validation, etc.). If working from raw SPEC.md, carve the spec into natural sections (use existing markdown headings). One "chunk" = one audit subagent.

**Do not audit all requirements in one pass.** Each chunk is bounded enough for a focused check; combined, they overwhelm context.

### Step 2 — Dispatch gap-check subagents (one per chunk)

For each chunk, use the `Agent` tool with `subagent_type: "general-purpose"` and this prompt pattern:

```
You are a spec→code gap auditor. A user will rely on the code shipping what the spec promises.

**Your chunk** (requirements/flows/entities for this category):
<paste the chunk verbatim>

**Your job**: For each requirement in your chunk:
1. Find where the code should deliver it. Use Glob/Grep/Read.
2. Decide: does the code actually let an end user observe this requirement work?
3. If NO: record a gap.

**Test it like a user would.** If the spec says "a receptionist scans a day ticket," the check is not "does the enum include day_ticket" — it is "what happens when a day-ticket string hits the scan endpoint / scan screen?" Reach the user-facing surface and ask: will this actually behave correctly?

**Concrete tactics**:
- Schema/enum check: Grep for the value in the implementation (not just the schema).
- API check: Find the route handler. Read it. Does it handle this case or does it fall through to `unknown_token` / 500?
- UI check: Find the component. Read it. Does the element exist? Is it wired to the action?
- Flow check: Trace the user's steps end-to-end through the code. Any missing hop is a gap.

**Return EXACTLY this JSON** (no prose, no markdown fence, no commentary):
{
  "category": "<your chunk category>",
  "gaps": [
    {
      "req_id": "R12",
      "user_outcome": "<one sentence, user-framed, e.g. 'A day-ticket scan shows ADMIT on the station screen'>",
      "observed": "<what the code actually does when the user tries this>",
      "expected": "<what the spec says should happen>",
      "evidence_paths": ["<file>:<line>", ...],
      "proposed_fix": "<one sentence, concrete>",
      "complexity": "trivial|small|medium|large",
      "severity": "blocker|major|minor"
    }
  ]
}

Complexity rubric:
- trivial: one line / one enum value / one conditional
- small: one function body rewrite, ≤2 files touched
- medium: new function or component, ≤3 files
- large: new schema field, new route, new screen, or cross-cutting change

Return `{"category": "<cat>", "gaps": []}` if everything works. Do NOT invent gaps.
```

Dispatch all chunk subagents — one Agent tool call per chunk. Collect their JSON outputs.

### Step 3 — Consolidate into a gap report

Merge all subagent results into `${DIRIGENT_RUN_DIR}/polish-gap-report.json`:

```json
{
  "timestamp": "<ISO-8601>",
  "spec_source": "compact|raw",
  "chunks_audited": 6,
  "total_gaps_found": 11,
  "gaps": [
    { "req_id": "R12", "category": "api", "user_outcome": "...", "observed": "...", "expected": "...", "evidence_paths": [...], "proposed_fix": "...", "complexity": "small", "severity": "major" }
  ]
}
```

**Write this report even if you plan to apply zero fixes.** It is the audit output; the polish PLAN below is separate.

### Step 4 — Prioritize + cap

From the gap list, select the fixes to apply this invocation using BOTH axes:

1. **Severity-then-complexity sort**: `blocker` before `major` before `minor`; within severity, `trivial` before `small` before `medium`. Drop anything marked `large` — they belong in a new dirigent run, not polish.
2. **Per-invocation cap**: at most `--max-fixes` fixes (default 5).

Write `${DIRIGENT_RUN_DIR}/polish-PLAN.json`:

```json
{
  "timestamp": "<ISO-8601>",
  "fixes_planned": [
    { "req_id": "R12", "user_outcome": "...", "proposed_fix": "...", "complexity": "small", "severity": "major", "evidence_paths": [...] }
  ],
  "fixes_deferred": [
    { "req_id": "R19", "reason": "complexity=large — needs full plan/review cycle" }
  ]
}
```

### Step 5 — Apply fixes serially, one commit per fix

For each planned fix:

1. **Re-read the evidence_paths.** The gap report came from a subagent's view at audit time; the repo may have shifted since.
2. **Make the minimum change** that delivers the `user_outcome`. No refactoring, no surrounding cleanup, no abstractions. **Remember every file path you touch** — you will stage them explicitly below.
3. **Run the project's build/typecheck** (detect via `package.json` scripts / `pyproject.toml` / `Cargo.toml` / etc.). Must exit 0.
4. **Commit atomically, staging only the files you touched for THIS fix**:
   ```bash
   git add <path1> <path2> ...   # the specific files changed for this user_outcome — NEVER `git add -A` or `git add .`
   git commit -m "polish: <user_outcome in imperative form>

   Req: <req_id>
   Fixes gap: <observed> → <expected>
   "
   ```
   Staging by name matters: polish runs on third-party repos where the working tree may contain `.env`, credentials, large binaries, or other uncommitted work you must not sweep in.
5. If the build breaks after your change and you cannot fix it within one additional attempt, revert **only the files you just touched** with `git checkout -- <path1> <path2> ...` (never `git reset --hard` — it clobbers unrelated working-tree state). Record the fix in `fixes_abandoned[]` and move to the next.

**Do not batch fixes into one commit.** One commit per user-outcome keeps the closure audit and the git history interpretable.

### Step 6 — Closure audit (MANDATORY)

For each `req_id` in `fixes_planned`, dispatch a single small closure-check subagent with the same prompt shape as Step 2 but restricted to that one requirement. The question it answers: **does the code now deliver the user_outcome?**

Collect closure results into `${DIRIGENT_RUN_DIR}/polish-report.json`:

```json
{
  "timestamp": "<ISO-8601>",
  "fixes_applied": 3,
  "fixes_abandoned": 0,
  "fixes_deferred": 2,
  "closure_audit": [
    { "req_id": "R12", "verdict": "closed", "evidence": "station screen now shows ADMIT for DAY-* tokens" },
    { "req_id": "R7",  "verdict": "still_open", "evidence": "SMS intent button still has no click handler", "followup": "<one sentence>" }
  ],
  "summary": "<one paragraph, user-framed>"
}
```

**A fix that committed but didn't actually close the gap is still an open gap.** Mark it `still_open` honestly. This is the skill's integrity layer.

## Output files

| File | Purpose |
|---|---|
| `${DIRIGENT_RUN_DIR}/polish-gap-report.json` | Raw audit from Step 3, full gap list, always written |
| `${DIRIGENT_RUN_DIR}/polish-PLAN.json`       | What you chose to fix this run, written before Step 5 |
| `${DIRIGENT_RUN_DIR}/polish-report.json`     | Final closure audit + summary, written after Step 6 |

## Rules

<rules>
<rule>User-outcome first: every gap and every fix is framed as "what a user can now do / can't do" — not "what the endpoint returns" or "what the schema enumerates"</rule>
<rule>Subagents ONLY audit; the main agent applies fixes and runs the closure audit dispatch</rule>
<rule>One commit per fix, messaged with the user_outcome in imperative form</rule>
<rule>Never fabricate a closure_audit verdict — if a gap isn't actually closed by the commit, record still_open</rule>
<rule>`complexity: large` is always deferred — polish does not do new schema fields, new routes, new screens, or cross-cutting changes</rule>
<rule>If SPEC.compact.json is missing and you can't trivially regenerate it, proceed with raw SPEC.md — do not block the whole polish run on compaction</rule>
<rule>If the build is already broken at invocation start (fails before any polish fix), report that in polish-report.json summary and exit without applying fixes — polish does not fix pre-existing broken builds</rule>
<rule>Do NOT commit .dirigent/ or any polish-* artifacts to the target repo — they live in $DIRIGENT_RUN_DIR only</rule>
</rules>

## Constraints

<constraints>
<constraint>Max fixes per invocation: respect `--max-fixes` (default 5); prefer fewer, higher-quality fixes over more</constraint>
<constraint>Max time: ~30 minutes. Audit subagents should each be under 3 minutes</constraint>
<constraint>No new skills, no new abstractions, no new config files — polish edits existing code or does nothing</constraint>
<constraint>If the repo has uncommitted working-tree changes when polish starts, stop immediately and tell the user to commit or stash first</constraint>
</constraints>
