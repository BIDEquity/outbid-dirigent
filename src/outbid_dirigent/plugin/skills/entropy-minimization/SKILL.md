---
name: entropy-minimization
description: Align code and documentation, remove dead code, resolve contradictions after execution
context: fork
agent: doc-cleaner
---

# Entropy Minimization

You are a cleanup agent with a fresh context. Your job is to reduce entropy in the repository after a long execution session. The executing agents changed behavior, added features, and modified code — but they did NOT update all the documentation, remove stale references, or clean up dead code. You fix what they left behind.

## Why This Matters

After every long-running agent session, the repository accumulates entropy:
- Function X now has behavior B, but all docs still describe behavior A
- A module was renamed but 3 skill files still reference the old name
- A CLI flag was added but README doesn't list it
- An import references a function that was moved
- A schema gained new fields but the architecture doc shows the old fields
- Dead code remains from a refactor that replaced it

Repeat this across 10 sessions and the repository becomes unmaintainable. Agents start making poor decisions because their context (docs, comments, type hints) contradicts reality.

## Scope

Check `$ARGUMENTS` for scope:
- `--scope changed` (default): Only scan files changed in recent commits on this branch
- `--scope full`: Scan the entire repository

To determine "recent commits", use:
```bash
git log --oneline --no-merges -20 --format="%H" | head -20
```

For `--scope changed`, get the changed files:
```bash
git diff --name-only HEAD~20 HEAD 2>/dev/null || git diff --name-only $(git rev-list --max-parents=0 HEAD) HEAD
```

## Scan Checklist

Work through each category. For each issue found, fix it immediately — do not accumulate a list and fix later. Fix as you go.

### 1. Documentation vs Code

For every documentation file (README.md, ARCHITECTURE.md, CONTRIBUTING.md, docs/**/*.md):

**Check these concrete things:**
- CLI flags documented match actual `add_argument()` / argparse / click definitions
- Module/file lists match what actually exists in the directory
- Route/pipeline diagrams match actual step definitions in code
- Schema/model descriptions match actual Pydantic/dataclass fields
- Example commands and outputs are still valid
- Feature descriptions match current behavior
- Numbers and counts ("15 commands", "3 routes") match reality

**How to check:** For each claim in the doc, find the code that backs it. If you can't find the code, the doc is wrong.

### 2. Plugin/Skill Manifest Consistency

For plugin systems (plugin.json, package.json workspaces, monorepo configs):

- Every file referenced in the manifest exists
- Every file that should be in the manifest IS in the manifest
- Skill/command descriptions match what the skill actually does
- Skill instructions don't reference files, schemas, or classes that moved or were renamed

### 3. Dead Code

Scan for:
- Functions/methods defined but never called (grep for the function name across the codebase)
- Imports that are unused (the imported name never appears after the import line)
- Variables assigned but never read
- Files that nothing imports or references
- Config entries that no code reads
- TODO/FIXME comments that reference completed work

**Be conservative with dead code removal.** Only remove if you can verify it's truly unused. If a function might be called dynamically (e.g., via getattr, string dispatch, or CLI entry points), leave it.

### 4. Cross-Reference Integrity

Check that references between files are valid:
- Import paths resolve to actual modules
- File path strings in code point to files that exist
- Schema class names in skill docs match actual class names in code
- Error messages reference correct function/variable names
- Docstrings reference correct parameter names

### 5. Stale Comments and Docstrings

- Comments describing behavior that code no longer exhibits
- Docstrings with wrong parameter names or return types
- "TODO" items that have been done
- "HACK"/"WORKAROUND" comments where the underlying issue was fixed
- HTML entities in markdown/text (e.g. `&amp;&amp;` instead of `&&`)

### 6. Consistency

- Same concept described differently in different places (e.g., "3 routes" in README vs "5 routes" in ARCHITECTURE.md)
- Enum values, config keys, or constants that changed but weren't updated everywhere
- Mixed naming conventions for the same thing (e.g., `test_harness` vs `testHarness`)

## Output

After fixing everything, write `${DIRIGENT_RUN_DIR}/entropy-report.json`:

```json
{
  "timestamp": "ISO-8601",
  "scope": "changed|full",
  "files_scanned": 42,
  "issues_fixed": 8,
  "issues_remaining": 0,
  "fixes": [
    {
      "file": "README.md",
      "category": "doc_vs_code",
      "description": "Updated CLI flags table — was missing 12 of 21 flags",
      "severity": "medium"
    }
  ],
  "remaining": []
}
```

Severity levels:
- `critical`: Code references that would cause runtime errors (broken imports, missing files)
- `medium`: Documentation contradictions that would mislead agents or developers
- `low`: Cosmetic issues (stale comments, minor inconsistencies)

## Commit

After all fixes:
```bash
git add -A && git commit -m "chore: entropy minimization — align docs and code"
```

If there are no issues to fix, do NOT create an empty commit. Report `issues_fixed: 0` and exit.

## Rules

<rules>
<rule>Fix as you go — do not accumulate a list of issues to fix at the end</rule>
<rule>Every fix must be minimal and focused — do not refactor working code</rule>
<rule>Do not add new features, new documentation sections, or new abstractions</rule>
<rule>Do not change code behavior — only change documentation, comments, and dead code</rule>
<rule>If a doc says "3 things" but there are actually 5, update the doc to say 5 — do not remove the 2 extra things from code</rule>
<rule>When removing dead code, verify it is truly dead by searching for ALL references (including string references, dynamic dispatch, and test files)</rule>
<rule>When fixing a doc, read the current code first — never assume you know what it says</rule>
<rule>The report JSON must be valid JSON written to ${DIRIGENT_RUN_DIR}/entropy-report.json</rule>
<rule>If no issues found, exit cleanly with issues_fixed: 0. This is a success, not a failure.</rule>
</rules>

## Constraints

<constraints>
<constraint>No behavior changes — only documentation, comments, dead code, and cross-references</constraint>
<constraint>No new files except ${DIRIGENT_RUN_DIR}/entropy-report.json</constraint>
<constraint>Maximum 15 minutes — prioritize critical and medium issues over low</constraint>
</constraints>
