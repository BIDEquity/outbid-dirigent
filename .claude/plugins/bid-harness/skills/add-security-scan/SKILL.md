---
name: add-security-scan
description: Use when asked to 'add dependency scanning', 'set up CVE scanning', 'configure Dependabot', or when assess flags Section 08 CVE scanning rows as failing.
---

Add dependency vulnerability scanning to this repository's CI pipeline.

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 08 · Security & Dependency Management` to understand which scanning items are currently failing.

## Instructions

1. **Detect CI provider** (same logic as `/add-ci`): `.github/` → GitHub Actions; `.gitlab-ci.yml` → GitLab CI; `Jenkinsfile` → Jenkins; `.circleci/` → CircleCI. Default to GitHub Actions if nothing is detected.

2. **Detect the package ecosystem** from project files:

   | File present | Ecosystem |
   |---|---|
   | `package.json` | npm |
   | `pyproject.toml` or `requirements.txt` | pip |
   | `go.mod` | gomod |
   | `pom.xml` | maven |
   | `build.gradle` or `build.gradle.kts` | gradle |

3. **GitHub Actions repos — create `.github/dependabot.yml`** only if it does not already exist:

   ```yaml
   version: 2
   updates:
     - package-ecosystem: "[detected ecosystem]"
       directory: "/"
       schedule:
         interval: "weekly"
       open-pull-requests-limit: 5
   ```

   If multiple ecosystems are detected, add one `updates` entry per ecosystem.

4. **Add a `security` job to the CI pipeline.** Run the stack-appropriate scanner and block on critical/high CVEs:

   | Stack | Security scan command |
   |-------|----------------------|
   | TypeScript/JS | `npm audit --audit-level=high` |
   | Python | `pip install pip-audit && pip-audit --desc` |
   | Go | `go install golang.org/x/vuln/cmd/govulncheck@latest && govulncheck ./...` |
   | Java (Maven) | `mvn org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7` |
   | Java (Gradle) | `./gradlew dependencyCheckAnalyze` (requires `org.owasp.dependencycheck` plugin) |

   **GitHub Actions job to add to `.github/workflows/ci.yml`:**

   ```yaml
   security:
     name: Security Scan
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - name: Set up [language]
         # Same setup step as the test job
       - name: Install dependencies
         run: [detected install command]
       - name: Dependency vulnerability scan
         # Blocks the build on any critical or high-severity CVE
         run: [detected scan command from table above]
   ```

   For GitLab CI, Jenkins, and CircleCI: add the equivalent stage using the same scan command.

5. Output a summary:

   ```
   Security scanning configured.

   Files created/modified:
     [list each file]

   The security job blocks merges on any critical or high CVE.
   Next step: run /security-audit to check for OWASP Top 10 issues and hardcoded secrets.
   ```

## Update the status file

After adding dependency scanning, update `harness-docs/standards-status.md`:

1. Find the section heading `## 08 · Security & Dependency Management`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/add-security-scan`, Notes to the files created:
   - Row matching "Run dependency vulnerability scanning in CI on every build"
   - Row matching "Critical and high-severity CVEs block merges to main"
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `08 · Security & Dependency Management` row.
