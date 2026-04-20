---
name: setup-dev
description: Use when asked to 'set up local dev', 'get this running locally', 'install dependencies and run the app', 'generate a local setup runbook', or when a developer new to the repo wants to run it on their machine.
---

Help a developer run this repository locally. Detect what the repo needs, infer answers from existing files, ask the developer one question at a time for anything unknown, then either execute the setup or write a runbook.

## Modes

- `/setup-dev` — **setup mode** (default). Detect, infer, ask, execute, verify, write runbook.
- `/setup-dev runbook` — **runbook-only mode**. Detect, infer, ask, write runbook. Execute nothing.

If the developer's intent is unclear, ask once: "Do you want me to execute the setup, or just write a runbook?"

## Instructions

### Step 1 — Build the setup manifest

Scan the repository in this order. Record each concern as resolved or unknown.

| Concern | Sources to check (in order) |
|---|---|
| **Runtime** | Harness-detected stack in `CLAUDE.md` (between `<!-- BEGIN:bid-harness -->` markers); then `go.mod`, `package.json` `engines`, `pyproject.toml`, `pom.xml`, `Package.swift` |
| **Dep install command** | `package-lock.json` → `npm ci`; `yarn.lock` → `yarn install --frozen-lockfile`; `pnpm-lock.yaml` → `pnpm install --frozen-lockfile`; `go.sum` → `go mod download`; `poetry.lock` → `poetry install`; `requirements.txt` → `pip install -r requirements.txt`; `pom.xml` → `mvn -B dependency:go-offline`; `build.gradle` / `build.gradle.kts` → `./gradlew dependencies` |
| **Env config** | `.env.example`, `.env.sample`, `.env.template` (copy to `.env`); existing `.env` (verify required keys, do not overwrite) |
| **Services** | `docker-compose.yml` or `docker-compose.yaml` (→ `docker compose up -d`); README mentions of Postgres, Redis, MySQL, Kafka, RabbitMQ (→ flag as unknown) |
| **Start command** | `scripts.start` or `scripts.dev` in `package.json`; Makefile targets `run`, `dev`, `start`; README code fences containing `go run`, `python -m`, `./gradlew bootRun`, `mvn spring-boot:run`, `uvicorn`, `flask run`, `rails s` |

### Step 2 — Inference pass for unknowns

For each unknown, try to resolve from (in order): `README.md`, `.env.example`, `.github/workflows/*`, `docker-compose.yml`, `Makefile`. Only after inference fails does the concern become a **developer question**.

### Step 3 — Ask developer questions one at a time

For every remaining unknown, ask **one question at a time** in a conversational flow. State what you need and why. Example:

> I found `.env.example` with `DATABASE_URL` but no default value. What should I set it to for local dev? (Or say `manual` if you'll set it yourself later.)

If the developer answers `manual` or says they don't have the value, record the step as a manual step in the runbook and continue.

### Step 4 — Confirm the plan

Before executing anything, show the developer the full ordered step list:

```
1. npm ci
2. cp .env.example .env  (DATABASE_URL = postgres://localhost:5432/app)
3. docker compose up -d
4. npm run dev  (verify: open http://localhost:3000)
```

Ask: "Run this? [Y/n/runbook-only]". On `runbook-only`, skip Steps 5 and 6 — go directly to Step 7.

### Step 5 — Execute (setup mode only)

Run each step using the Bash tool. Capture output. **On any failure, stop and ask the developer:**

> Step N (`<command>`) failed:
> ```
> <error output>
> ```
> Options: retry / skip / abort. What would you like to do?

Never silently swallow failures. Continue only after the developer chooses.

### Step 6 — Verify (setup mode only)

For the start command:
- **Long-running process (server/worker):** run it in the background, wait up to 30 seconds for a health signal — either the configured port accepts connections, or stdout contains a line matching `listening|ready|started`. Then stop the process.
- **One-shot CLI:** run `<binary> --help` or `<binary> --version` to confirm it executes.

If verify fails, record the error in the runbook's Troubleshooting section.

### Step 7 — Write the runbook

Always write `harness-docs/local-dev-setup.md` using the Write tool (overwriting any existing file). Use this exact format:

````
<!-- generated_by: /setup-dev -->
<!-- generated_at: YYYY-MM-DD -->

# Local Development Setup

_Last updated: YYYY-MM-DD · regenerate with `/setup-dev runbook`_

## Prerequisites

- [runtime] <detected runtime and version, e.g. Node 20+>
- [services] <e.g. Docker Desktop running> (only if docker-compose step exists)
- [tools] <any required CLI tools>

## 1. Install dependencies

```bash
<dep install command>
```

## 2. Environment configuration

```bash
cp .env.example .env
```

Required variables:

| Variable | Purpose | Example |
|---|---|---|
| `VAR_NAME` | <purpose> | `<example or — >` |

(Rows with unresolved values show `**MANUAL STEP: <why>**` in the Example column.)

## 3. Start supporting services

```bash
<service command or "No supporting services required.">
```

## 4. Run the app

```bash
<start command>
```

Health check: <URL or "process stays up — Ctrl+C to stop">.

## Troubleshooting

<only populated if verify failed or a step errored — otherwise omit this section>
````

Skip any section that does not apply (e.g., omit section 3 if there are no services).

### Step 8 — Summary

After writing the runbook, print a short summary:

```
## Setup complete

- Runbook written: harness-docs/local-dev-setup.md
- Steps executed: <N>/<M>
- Manual steps remaining: <list, or "none">

Next: commit harness-docs/local-dev-setup.md so the whole team benefits.
```

In runbook-only mode the `Steps executed` line is omitted.

## Out of scope

- Windows / WSL-specific branches. Assume macOS or Linux.
- Orchestrating version managers (`asdf`, `nvm`, `pyenv`). Verify the runtime exists at the expected major version and report if missing.
- Running tests. Use `/test-bootstrap` or the project's own test command.
