---
name: add-release
description: Use when asked to 'add a release pipeline', 'automate versioning', 'set up semantic-release', 'configure release-please', or when release automation is missing from a CI-configured repository.
---

Generate a release pipeline configuration for this repository.

## Usage

- `/add-release` — auto-detect release tool and CI provider

## Before you begin

Check if `harness-docs/standards-status.md` exists in this repository.
- If it does **not** exist: run `/assess` first to establish a baseline, then return here and continue.
- If it exists: read the rows for `## 05 · Continuous Delivery & CI/CD` (specifically the Commit Conventions & Versioning items) to understand which release items are currently failing.

## Instructions

1. **Detect the CI provider:**
   - Check: `.github/` present → GitHub Actions; `.gitlab-ci.yml` exists → GitLab CI; `Jenkinsfile` exists → Jenkins; `.circleci/` exists → CircleCI
   - If nothing detected: default to GitHub Actions; note the assumption in the output

2. **Detect the release tool:**
   - If `package.json` exists in the repo root → use **`semantic-release`** (Node-native)
   - Otherwise → use **`release-please`** (stack-agnostic, GitHub Actions native)

3. **Detect the stack** from the loaded CLAUDE.md context or from project files (used to set the `release-type` for `release-please`). **Only perform this step if step 2 resolved to `release-please`. If the tool is `semantic-release`, skip to step 10.**

---

### If release tool is `release-please` (non-Node repos)

4. **Determine the `release-type`** based on detected stack:

   | Stack | `release-type` |
   |-------|----------------|
   | Go (`go.mod` present) | `go` |
   | Python (`pyproject.toml` or `setup.py` present) | `python` |
   | Java with Maven (`pom.xml` present) | `maven` |
   | Java with Gradle (`build.gradle` present) | `java-yoshi` |
   | Everything else | `simple` |

5. **GitLab CI special case:** If the CI provider is GitLab, first check whether `package.json` exists in the repo root.

   - **If `package.json` does not exist:** Output a note:

     ```
     Note: release-please has limited native GitLab support, and semantic-release requires Node.js (no package.json found).
     This stack is not suitable for semantic-release. Recommended stack-native alternatives:
       - Go: GoReleaser (goreleaser.com)
       - Python: python-semantic-release
       - Java: JReleaser (jreleaser.org)
       - Other: manual versioning or a CI-native release mechanism
     ```

     Stop here — do not generate any config files.

   - **If `package.json` exists:** Output a note:

     ```
     Note: release-please has limited native GitLab support. For GitLab repos,
     semantic-release with @semantic-release/gitlab is recommended instead.
     Generating a .releaserc.json with the GitLab plugin.
     ```

     Then generate only the `.releaserc.json` with the GitLab plugin (see step 11 below for the GitLab `.releaserc.json` format). Skip generating the workflow file.

6. **Jenkins / CircleCI special case:** If the CI provider is Jenkins or CircleCI, first check whether `package.json` exists in the repo root.

   - **If `package.json` does not exist:** Output a note:

     ```
     Note: semantic-release requires Node.js (no package.json found).
     This stack is not suitable for semantic-release. Recommended stack-native alternatives:
       - Go: GoReleaser (goreleaser.com)
       - Python: python-semantic-release
       - Java: JReleaser (jreleaser.org)
       - Other: manual versioning or a CI-native release mechanism
     ```

     Stop here — do not generate any config files.

   - **If `package.json` exists:** Output a note:

     ```
     Note: Automated release tooling integration varies significantly by Jenkins/CircleCI setup.
     Recommend configuring semantic-release manually using your CI's secret management.
     Generating .releaserc.json only — wire it up in your pipeline yourself.
     ```

     Then generate only `.releaserc.json` (the semantic-release format from step 11). Skip generating the workflow file.

**If you executed step 5 or step 6, stop here — do not proceed to the release-please or semantic-release steps below.**

7. **Write `.github/workflows/release.yml`** (GitHub Actions only) using the Write tool. **Before writing, check if `.github/workflows/release.yml` already exists. If it does, read its contents and ask the user whether to overwrite it before proceeding.**

   ```yaml
   name: Release

   on:
     push:
       branches: [main]

   jobs:
     release-please:
       name: Release Please
       runs-on: ubuntu-latest
       permissions:
         contents: write
         pull-requests: write
       steps:
         - uses: google-github-actions/release-please-action@v4
           with:
             token: ${{ secrets.GITHUB_TOKEN }}
   ```

8. **Write `release-please-config.json`** only if it does not already exist:

   ```json
   {
     "release-type": "[same release-type as above]",
     "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
   }
   ```

9. **Write `.release-please-manifest.json`** only if it does not already exist:

   ```json
   {
     ".": "0.0.0"
   }
   ```

---

### If release tool is `semantic-release` (Node repos, or GitLab fallback from step 5)

10. **Write `.github/workflows/release.yml`** (GitHub Actions only; skip for GitLab/Jenkins/CircleCI) using the Write tool. **Before writing, check if `.github/workflows/release.yml` already exists. If it does, read its contents and ask the user whether to overwrite it before proceeding.**

    ```yaml
    name: Release

    on:
      push:
        branches: [main]

    jobs:
      release:
        name: Semantic Release
        runs-on: ubuntu-latest
        permissions:
          contents: write
          issues: write
          pull-requests: write
        steps:
          - uses: actions/checkout@v4
            with:
              fetch-depth: 0
              persist-credentials: false
          - uses: actions/setup-node@v4
            with:
              node-version: '20'
          - name: Install dependencies
            run: npm ci
          - name: Release
            # Reads commits since last tag, bumps version, publishes release and CHANGELOG
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              # NPM_TOKEN: ${{ secrets.NPM_TOKEN }}  # Uncomment if publishing to npm
            run: npx semantic-release
    ```

11. **Check for an existing semantic-release config** before writing one. Look for any of: `.releaserc`, `.releaserc.json`, `.releaserc.js`, `release.config.js`, or a `release` key in `package.json`. Only if none of these exist, write `.releaserc.json` using the Write tool.

    **For GitHub Actions / GitHub repos:**

    ```json
    {
      "branches": ["main"],
      "plugins": [
        "@semantic-release/commit-analyzer",
        "@semantic-release/release-notes-generator",
        "@semantic-release/changelog",
        ["@semantic-release/npm", { "npmPublish": false }],
        ["@semantic-release/github"],
        ["@semantic-release/git", {
          "assets": ["CHANGELOG.md", "package.json"],
          "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
        }]
      ]
    }
    ```

    **For GitLab repos** (the GitLab fallback path from step 5):

    ```json
    {
      "branches": ["main"],
      "plugins": [
        "@semantic-release/commit-analyzer",
        "@semantic-release/release-notes-generator",
        "@semantic-release/changelog",
        ["@semantic-release/gitlab"],
        ["@semantic-release/git", {
          "assets": ["CHANGELOG.md"],
          "message": "chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
        }]
      ]
    }
    ```

---

12. **After writing all files**, output:

    ```
    Release workflow written.

    Files created:
      [list each file written]

    Next steps:
      1. Set the required secrets in your repository settings:
         - GitHub: GITHUB_TOKEN is auto-provided; NPM_TOKEN only needed if publishing to npm
         - For release-please: no extra secrets needed beyond GITHUB_TOKEN
      2. Commit and push:
           git add [files]
           git commit -m "ci: add automated release pipeline"
           git push
      3. The first release will be cut on the next merge to main that includes a feat or fix commit.
      4. Review CHANGELOG.md after the first release — it is auto-generated from commit history.
    ```

## Update the status file

After writing release configuration files, update `harness-docs/standards-status.md`:

1. Find the section heading `## 05 · Continuous Delivery & CI/CD`.
2. For each row below where the corresponding artefact was created, update Status to `✅ PASS`, Verified to today's date, Fixed By to `/add-release`, Notes to the files created:
   - Row matching "Use Conventional Commits for all commit messages" (if commitlint config was created)
   - Row matching "Enforce Conventional Commits via a commit-msg hook in CI" (if commitlint job was added to the pipeline)
   - Row matching "All repositories must follow Semantic Versioning"
   - Row matching "Automate version bumping on every merge to main"
   - Row matching "Automatically generate or update a CHANGELOG.md from commit history"
3. Recalculate the MUST ✅ and MUST ❌ totals in the Summary table for the `05 · Continuous Delivery & CI/CD` row.
