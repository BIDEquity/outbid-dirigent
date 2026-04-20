---
name: test-bootstrap
description: Use when asked to 'generate tests', 'bootstrap a test suite', 'add initial tests', or when source files exist with no corresponding test files.
---

Generate an initial test suite for untested code in this repository.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 04 · Test Strategy` to understand which testing items are currently failing before generating tests.

## Usage

- `/test-bootstrap` — scan the entire repo
- `/test-bootstrap src/payments/` — focus on a specific path

## Instructions

1. **Determine the scope.** If a path argument was given, limit the scan to that path. Otherwise scan the full repo.

2. **Identify the stack** from the loaded CLAUDE.md context, or by inspecting project files (`package.json`, `go.mod`, `pyproject.toml`, `pom.xml`).

3. **Find untested source files.** A file is considered untested if no corresponding test file exists adjacent to it or in a parallel `__tests__/` / `tests/` directory.

   Prioritise files by:
   - Number of exported/public function or class definitions (more = higher priority)
   - Domain-suggestive names (e.g. `payment`, `order`, `auth`, `user`) over infrastructure names (`config`, `logger`, `utils`)
   - Entry points: files imported by many others, route handlers, service classes

   Exclude: generated files, database migrations, config files, vendored or third-party code.

   Select the **3–5 highest-priority untested files** per run. If the scope path was given, use all files in that path.

4. **For each selected file**, generate a test file:

   | Stack | Framework | Test file location |
   |-------|-----------|-------------------|
   | TypeScript/JS | vitest (preferred) or jest | `<filename>.test.ts` next to source |
   | Python | pytest | `test_<filename>.py` next to source, or in `tests/` |
   | Go | stdlib `testing` | `<filename>_test.go` next to source |
   | Java | JUnit 5 | `<ClassName>Test.java` in matching `src/test/` path |

   For each public function or method in the file, write:
   - One test for the happy path (normal inputs, expected output)
   - One test for a meaningful edge case or error condition

   Mock only at system boundaries (HTTP clients, database connections, filesystem). Do not mock internal modules.

   Use descriptive test names: `it("returns null when user is not found")` not `it("works")`.

5. **Write the generated test files** using the Write tool.

6. **Output a summary table** — do not run the tests:

   ```
   ## Test Bootstrap Summary

   Generated N test files covering Y functions.

   | Source file | Test file | Functions covered |
   |-------------|-----------|-------------------|
   | src/auth.ts | src/auth.test.ts | login, logout, refreshToken |

   ## Flagged — too complex to test safely without refactoring first
   | File | Reason |
   |------|--------|
   | src/legacy/processor.ts | 400-line file with 20+ responsibilities — run `/refactor-plan src/legacy/processor.ts` first |

   ## Next step
   Run the test suite: [stack-specific command — e.g. `npx vitest run` / `pytest` / `go test ./...` / `mvn test`]
   ```

## Update the status file

After writing test files, update `harness-docs/standards-status.md`:

1. Find the section heading `## 04 · Test Strategy`.
2. For each row below where the corresponding test files were generated, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/test-bootstrap`, Notes to the number of test files created:
   - Row matching "Cover business logic with unit tests that run in CI on every commit"
   - Row matching "Cover key interaction points ... with integration tests in CI" (only if integration tests were generated)
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `04 · Test Strategy` row.
