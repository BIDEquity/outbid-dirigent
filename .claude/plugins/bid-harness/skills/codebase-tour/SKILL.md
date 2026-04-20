---
name: codebase-tour
description: Use when asked to 'create a codebase tour', 'document how this codebase works', 'write an orientation guide for new engineers', or 'generate an onboarding walkthrough'.
---

Generate an onboarding walkthrough document for engineers who are new to this repository.

## Instructions

1. **Explore the repository** before writing anything: read the directory structure, entry points, key source files, and any existing documentation (`README.md`, `harness-docs/adr/`, `CONTRIBUTING.md`).

2. **Write `harness-docs/codebase-tour.md`** using the Write tool. If the file already exists, update rather than replace it.

   Document structure:

   ```markdown
   # Codebase Tour

   _For engineers who know [detected language] but are new to this codebase._
   _Last updated: [date]_

   ## What this system does

   [2–3 sentences: the purpose of the system, who or what consumes it, and the core problem it solves. Infer from README, package name, and source code if no README exists.]

   ## How the code is organised

   [Annotated directory tree, 2 levels deep. One-line description per top-level directory.]

   ```
   src/
     api/        HTTP route handlers — entry points for all requests
     services/   Business logic — no framework dependencies
     db/         Database access layer — Postgres via pg
   tests/        Unit and integration tests (vitest)
   ```

   ## Key flows

   [2–4 of the most important request or processing flows. Each as a numbered sequence showing which files/functions are involved.]

   ### Flow: [name, e.g. "User signs up"]
   1. `src/api/auth.ts → POST /signup` — validates request body
   2. `src/services/user.service.ts → createUser()` — hashes password, persists user
   3. `src/db/user.repo.ts → insert()` — writes to `users` table
   4. Returns 201 with JWT

   ## Entry points

   [Where does execution start? List the main file, CLI entrypoint, or top-level handler for each distinct execution mode.]

   | Mode | Entry point |
   |------|-------------|
   | HTTP server | `src/index.ts` |
   | CLI | `src/cli.ts` |

   ## Ownership

   [If `CODEOWNERS` exists, summarise it. Otherwise, list the top 3 directories and their most recent committers based on git blame.]

   ## Known gotchas

   [Non-obvious things that trip up new engineers. Examples: environment variables required before the app starts, files generated at build time that should not be edited, implicit conventions not documented elsewhere.]

   ## Where to start reading

   [Ordered list of 3–5 files a new engineer should read first to build a mental model of the system.]

   1. `src/index.ts` — startup and dependency wiring
   2. `src/services/order.service.ts` — core domain logic
   3. `src/db/schema.ts` — data model
   ```

3. Output a one-line confirmation:

   ```
   docs/codebase-tour.md written — [N] sections, [X] key flows documented.
   ```
