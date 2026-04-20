---
name: test-coverage
description: Use when asked to 'run test coverage', 'check code coverage', 'show coverage report', 'how much test coverage do we have', or 'what is our coverage percentage'.
---

Run the test suite with coverage reporting.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 04 · Test Strategy` to understand which coverage-related items are currently failing.

## Instructions

1. **Detect the stack** from the loaded CLAUDE.md context, or by inspecting project files:
   - `go.mod` present → Go
   - `package.json` present → TypeScript/JavaScript
   - `pyproject.toml` or `requirements.txt` present → Python
   - `pom.xml` present → Java (Maven)
   - `build.gradle` or `build.gradle.kts` present → Java (Gradle)
   - `Package.swift` present → Swift

2. **Run the appropriate coverage command:**

   **Go:**
   ```
   go test ./... -coverprofile=coverage.out -covermode=atomic
   go tool cover -func=coverage.out
   ```
   Clean up: remove `coverage.out` after reporting.

   **TypeScript/JavaScript:**
   - Check `package.json` scripts for test commands
   - Look for `vitest.config.ts`, `jest.config.ts`, or equivalent
   - Vitest: `npx vitest run --coverage`
   - Jest: `npx jest --coverage`

   **Python:**
   - Check `pyproject.toml` for `[tool.pytest]` or `[tool.pytest.ini_options]`
   - Check for `pytest.ini`, `setup.cfg`, or `tox.ini`
   - Run: `pytest --cov --cov-report=term-missing --cov-fail-under=70`
   - Adjust the `--cov` path if the source package is configured in pyproject.toml.

   **Java (Gradle):**
   ```
   ./gradlew test jacocoTestReport
   ```
   Read the JaCoCo report at `build/reports/jacoco/test/html/index.html`.

   **Java (Maven):**
   ```
   ./mvnw test jacoco:report
   ```
   Read the JaCoCo report at `target/site/jacoco/index.html`.

   **Swift:**
   ```
   swift test --enable-code-coverage
   ```
   Then locate the profile data and generate the report:
   ```
   PROFDATA=$(find .build -name "default.profdata" 2>/dev/null | head -1)
   # On macOS: binary is inside an .xctest bundle
   XCTEST=$(find .build/debug -maxdepth 2 -name "*.xctest" 2>/dev/null | head -1)
   if [ -n "$XCTEST" ]; then
       EXEC="$XCTEST/Contents/MacOS/$(basename "${XCTEST%.xctest}")"
   else
       # Linux: find the test executable directly
       EXEC=$(find .build/debug -maxdepth 2 -name "*PackageTests" -type f 2>/dev/null | head -1)
   fi
   xcrun llvm-cov report "$EXEC" \
     --instr-profile="$PROFDATA" \
     --ignore-filename-regex=".build|Tests"
   ```

3. **Report results:**
   - Total coverage percentage
   - Files/packages/classes with lowest coverage
   - Functions or lines with zero coverage
   - Whether the coverage threshold (70% default, or project-configured threshold) was met

4. If tests fail, report failures first before coverage results.

## Update the status file

After configuring coverage reporting, update `harness-docs/standards-status.md`:

1. Find the section heading `## 04 · Test Strategy`.
2. Find the row matching "Measure and report code coverage in CI" (Level: REC). Update it: Status → `✅ PASS`, Verified → today's date, Fixed By → `/test-coverage`, Notes → the coverage tool and threshold configured.
3. Recalculate the REC ✅ and REC ❌ totals in the Summary table for the `04 · Test Strategy` row.
