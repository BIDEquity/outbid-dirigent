---
name: add-ci
description: Use when asked to 'add CI', 'set up a pipeline', 'configure GitHub Actions', 'add CI/CD', or when no CI configuration is detected (.github/workflows/, .gitlab-ci.yml, Jenkinsfile, .circleci/).
---

Generate a CI pipeline configuration for this repository.

## Usage

- `/add-ci` — auto-detect provider
- `/add-ci github` — specify provider (`github`, `gitlab`, `jenkins`, `circleci`)

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 05 · Continuous Delivery & CI/CD` to understand which pipeline items are currently failing before generating configuration.

## Instructions

1. **Detect the CI provider:**
   - If a provider argument was given, use it
   - Otherwise check: `.github/` present → GitHub Actions; `.gitlab-ci.yml` exists → GitLab CI; `Jenkinsfile` exists → Jenkins; `.circleci/` exists → CircleCI
   - If nothing detected and no argument: default to GitHub Actions; note the assumption in the output

2. **Detect the stack** from the loaded CLAUDE.md context or from project files.

3. **Detect the actual tooling commands** by reading project files — do not use generic placeholders:

   | Stack | Lint | Test | Build |
   |-------|------|------|-------|
   | TypeScript | check `package.json` scripts for `lint`; default `npx eslint .` | check for `test` script; default `npx vitest run` | check for `build` script; default `npx tsc --noEmit` |
   | Python | check for `ruff.toml` → `ruff check .`; else `flake8 .` | check `pyproject.toml` for pytest config → `pytest`; else `python -m pytest` | `python -m build` if `pyproject.toml` present |
   | Go | `golangci-lint run` if `.golangci.yml` present; else `go vet ./...` | `go test ./...` | `go build ./...` |
   | Java | `mvn checkstyle:check` if `checkstyle.xml` present; else `mvn validate` | `mvn test` | `mvn package -DskipTests` |

   **Commitlint** always runs via Node regardless of stack — no stack-specific variation needed.

4. **Check for a commitlint config** in the repo root. Look for any of: `.commitlintrc.json`, `.commitlintrc.js`, `commitlint.config.js`, or a `commitlint` key in `package.json`. Only if none of these exist, create `.commitlintrc.json` with the Write tool:

   ```json
   {
     "extends": ["@commitlint/config-conventional"]
   }
   ```

5. **Generate the pipeline file(s)** using the Write tool. Write to the correct path for the provider:

   | Provider | Output path |
   |----------|-------------|
   | GitHub Actions | `.github/workflows/ci.yml` |
   | GitLab CI | `.gitlab-ci.yml` |
   | Jenkins | `Jenkinsfile` |
   | CircleCI | `.circleci/config.yml` |

   **GitHub Actions template** (adapt commands from step 3):

   ```yaml
   name: CI

   on:
     push:
       branches: [main, master]
     pull_request:

   jobs:
     lint:
       name: Lint
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Set up [language]
           # add stack-specific setup step here
         - name: Install dependencies
           run: [detected install command]
         - name: Lint
           # Checks code style and catches common errors before running tests
           run: [detected lint command]

     commitlint:
       name: Commitlint
       runs-on: ubuntu-latest
       if: github.event_name == 'pull_request'
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 50
         - uses: actions/setup-node@v4
           with:
             node-version: '20'
         - name: Install commitlint
           run: npm install --no-save @commitlint/cli @commitlint/config-conventional
         - name: Validate commit messages
           # Ensures all commits in this PR follow Conventional Commits format
           run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to ${{ github.event.pull_request.head.sha }} --verbose

     test:
       name: Test
       runs-on: ubuntu-latest
       needs: lint
       steps:
         - uses: actions/checkout@v4
         - name: Set up [language]
           # add stack-specific setup step here
         - name: Install dependencies
           run: [detected install command]
         - name: Test
           # Runs the full test suite — must pass before merging
           run: [detected test command]

     build:
       name: Build
       runs-on: ubuntu-latest
       needs: test
       steps:
         - uses: actions/checkout@v4
         - name: Set up [language]
           # add stack-specific setup step here
         - name: Install dependencies
           run: [detected install command]
         - name: Build
           # Verifies the project compiles/builds cleanly
           run: [detected build command]
   ```

   The `commitlint` job runs in parallel with `lint` (no `needs` dependency). It only runs on pull requests so it does not block push-to-main builds.

   Fill in the stack-specific setup step (e.g. `actions/setup-node@v4`, `actions/setup-python@v5`, `actions/setup-go@v5`, `actions/setup-java@v4`) with the version pinned to the project's runtime version where detectable.

   **GitLab CI template** (adapt commands from step 3):

   Add a `commitlint` job alongside the existing lint/test/build jobs:

   ```yaml
   commitlint:
     stage: lint
     image: node:20-alpine
     rules:
       - if: $CI_PIPELINE_SOURCE == "merge_request_event"
     script:
       - git fetch --depth=50 origin $CI_MERGE_REQUEST_DIFF_BASE_SHA
       - npm install --no-save @commitlint/cli @commitlint/config-conventional
       # Validates all commits in this MR against Conventional Commits format
       - npx commitlint --from $CI_MERGE_REQUEST_DIFF_BASE_SHA --to $CI_COMMIT_SHA --verbose
   ```

   **Jenkins template** (adapt commands from step 3):

   Add a `Commitlint` stage in the pipeline (runs only on pull requests via a `when` condition):

   ```groovy
   stage('Commitlint') {
     when { changeRequest() }
     steps {
       // Requires the NodeJS Pipeline Plugin and a 'Node 20' installation
       // configured in Jenkins → Manage Jenkins → Global Tool Configuration
       nodejs(nodeJSInstallationName: 'Node 20') {
         sh 'npm install --no-save @commitlint/cli @commitlint/config-conventional'
         // Validates all commits in this PR against Conventional Commits format
         sh "npx commitlint --from origin/${env.CHANGE_TARGET} --to HEAD --verbose"
       }
     }
   }
   ```

   Place this stage in parallel with (or immediately before) the Lint stage so it does not depend on lint/test/build results.

   **CircleCI template** (adapt commands from step 3):

   Add a `commitlint` job to the `jobs` map and include it in the workflow:

   ```yaml
   jobs:
     commitlint:
       docker:
         - image: cimg/node:20.0
       steps:
         - checkout
         - run:
             name: Install commitlint
             command: npm install --no-save @commitlint/cli @commitlint/config-conventional
         - run:
             name: Validate commit messages
             # Ensures all commits in this PR follow Conventional Commits format
             command: npx commitlint --from $(git merge-base HEAD origin/main) --to HEAD --verbose

   workflows:
     ci:
       jobs:
         - commitlint:
             filters:
               branches:
                 ignore: main   # fires on all feature-branch pushes — CircleCI has no native PR-only trigger without an orb; this approximates PR pipelines
                                # If the existing config already uses the `circleci/github` orb, use its `pr-filter` parameter instead of the branch filter.
         - lint
         - test:
             requires: [lint]
         - build:
             requires: [test]
   ```

6. After writing the file(s), output:

   ```
   Pipeline written to [path].
   [If .commitlintrc.json was created]: Commitlint config written to .commitlintrc.json.

   Jobs: lint · commitlint (PR-only) · test (needs: lint) · build (needs: test)

   Review it, then commit and push to activate:
     git add [path] [.commitlintrc.json if created]
     git commit -m "ci: add lint/commitlint/test/build pipeline"
     git push

   The pipeline will run on your next push to main or on any pull request.
   Commitlint will block merge if any commit message does not follow Conventional Commits format.
   ```

## Update the status file

After writing the pipeline file(s), update `harness-docs/standards-status.md`:

1. Find the section heading `## 05 · Continuous Delivery & CI/CD`.
2. For each row below, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/add-ci`, Notes to the pipeline file path created:
   - Row matching "Every repository must have a CI pipeline that runs on every commit: linting, unit tests, integration tests, and build validation"
   - Row matching "Keep the main branch always in a deployable state" (if the pipeline includes merge gates)
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `05 · Continuous Delivery & CI/CD` row.
