---
name: document-codebase
description: Use when asked to 'add documentation', 'improve the README', 'add doc comments', or when README is missing or public APIs are undocumented.
---

Generate documentation for this repository in three passes.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 03 · Code Quality, Reviews & Standards` to understand which documentation items are currently failing before generating content.

## Instructions

### Pass 1: README

Read the existing `README.md` if it exists.

- **Missing:** Create `README.md` with these sections: project name and one-sentence purpose, prerequisites, setup (how to install dependencies), how to run locally, how to run tests, deployment notes, links to `harness-docs/adr/` if it exists. Infer instructions from `package.json` scripts, `Makefile`, `go.mod`, `pyproject.toml`, or `pom.xml`.
- **Exists but sparse** (under 50 lines, or missing setup / test instructions): fill in the missing sections without removing existing content.
- **Already comprehensive:** skip this pass, note it in the summary.

### Pass 2: Module-level docs

Scan source files for public functions, classes, and exports that have no doc comment.

For each file missing documentation, add:
- A single file-level comment describing what the module does and its role in the system
- Doc comments on public functions/methods describing what it does, parameters (if non-obvious), and return value (if non-obvious)

Follow the language's doc comment style:
- TypeScript/JS: JSDoc (`/** ... */`)
- Python: docstrings (`"""..."""`)
- Go: Go doc comments (`// FunctionName ...`)
- Java: Javadoc (`/** ... */`)

Do not document private helpers unless they contain genuinely non-obvious logic.

**Limit to 10 files per run.** Start with the files most central to the system (imported most by others, or named after domain concepts).

### Pass 3: Flag complex code

Identify functions and classes that are too complex to document clearly without refactoring first:
- Functions over 50 lines
- Functions with deep nesting (3+ levels of if/for/try)
- Classes with more than 10 public methods

For each, add a single-line comment at the declaration:

```
// TODO(doc): complex — consider /refactor-plan before documenting
```

Do not attempt to write doc comments for these. List them in the summary.

### Summary

After all three passes, output:

```
## Documentation Summary

README:               [created | updated | already comprehensive — skipped]
Module docs added:    X files, Y functions/classes documented
Flagged for refactor: Z items (search TODO(doc) to find them)
```

## Update the status file

After writing documentation, update `harness-docs/standards-status.md`:

1. Find the section heading `## 03 · Code Quality, Reviews & Standards`.
2. If a README was created or substantially improved, find the row matching "Every repository must have a README" and update it: Status → `✅ PASS`, Verified → today's date, Fixed By → `/document-codebase`, Notes → "README created/updated with purpose, setup, tests, deployment, ADR links".
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `03 · Code Quality, Reviews & Standards` row.
