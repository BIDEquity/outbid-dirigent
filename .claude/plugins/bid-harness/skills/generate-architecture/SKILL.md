---
name: generate-architecture
description: Generate ARCHITECTURE.md — a complete, agent-readable map of the codebase that eliminates cold-start penalty for every agent session
---

# Generate Architecture

You produce `ARCHITECTURE.md` — a single file that gives any agent (or human) landing in this repo everything it needs to navigate and modify the codebase confidently.

## Why This Matters

Without an architecture doc, every agent session starts with 10-15 minutes of codebase exploration. Worse, agents make wrong assumptions about how modules connect, where data flows, and what patterns to follow. ARCHITECTURE.md eliminates this cold-start penalty.

This is NOT documentation for documentation's sake. Every section exists because an agent will need it to make better decisions.

## Relationship to ADRs

ARCHITECTURE.md is a **wrapper** over the repo's Architecture Decision Records. Treat it as a higher-order document:

- **ARCHITECTURE.md = the map.** What exists, how it connects, where things live, which patterns recur.
- **ADRs = the rationale.** *Why* a choice was made, what was considered, what the trade-offs are. The harness `/adr` skill writes them to `harness-docs/adr/NNNN-*.md`; pre-existing repos may use `docs/adr/`, `doc/adr/`, `adr/`, or `docs/architecture/decisions/` — Step 1f scans all of these.

Rules for the relationship:

1. **Never inline decision rationale** in ARCHITECTURE.md. If a "why" needs more than one sentence, it belongs in an ADR that ARCHITECTURE.md links to.
2. **Always reference ADRs** instead of restating them. The `## Architecture Decisions` section is an index of ADR links, not a place to duplicate content.
3. **Surface decision gaps.** If the survey reveals a significant decision that has no ADR, do not fabricate a rationale — record the gap and suggest the user run `/adr` to create one, then link it.
4. **Stay in sync.** When ADRs are added, updated, deprecated, or superseded, `/generate-architecture --update` refreshes the index to match.

## Mode

Check `$ARGUMENTS` for mode:
- **Default (generate)**: Create ARCHITECTURE.md from scratch
- **`--update`**: Read existing ARCHITECTURE.md, verify each section against current code, update what changed, preserve manually-written sections marked with `<!-- manual -->`

## Step 1: Survey the Codebase

Before writing anything, build a mental model:

### 1a. Identify the tech stack
```bash
# Package managers and dependencies
ls package.json pyproject.toml Cargo.toml go.mod pom.xml build.gradle Gemfile composer.json 2>/dev/null

# Frameworks — check actual imports, not just deps
grep -r "from fastapi\|from django\|from flask\|from express\|from next\|from nuxt\|from nest" --include="*.py" --include="*.ts" --include="*.js" -l | head -20
```

### 1b. Identify entry points
Every codebase has entry points — where execution starts. Find them:
- **CLI**: `main()`, `if __name__ == "__main__"`, `bin/` scripts, package.json `bin` field
- **Web**: route definitions, `app.py`, `server.ts`, `pages/`, `app/` directories
- **Workers**: queue consumers, cron definitions, Celery tasks, background jobs
- **Libraries**: public API surface, `__init__.py` exports, `index.ts` re-exports

### 1c. Map the module structure
```bash
# For Python
find . -name "*.py" -not -path "*/node_modules/*" -not -path "*/.venv/*" | head -50

# For TypeScript/JavaScript
find . -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v .next | head -50

# For monorepos
ls -d packages/*/package.json apps/*/package.json 2>/dev/null
```

### 1d. Identify data flow
- Where does data enter the system? (API endpoints, CLI args, message queues, file uploads)
- Where is data stored? (databases, caches, file system, external services)
- How does data move between modules? (function calls, events, queues, HTTP)

### 1e. Identify key patterns
Look for recurring patterns the codebase uses:
- Repository/service pattern
- Event-driven architecture
- Middleware chains
- Plugin/hook systems
- State machines
- Queue-based processing

### 1f. Find existing Architecture Decision Records

ARCHITECTURE.md points to ADRs rather than paraphrasing them, so you must know which ADRs already exist before writing. Scan the common locations:

```bash
# Harness default (written by the /adr skill)
ls harness-docs/adr/*.md 2>/dev/null

# Pre-existing conventions in target repos
ls docs/adr/*.md doc/adr/*.md adr/*.md 2>/dev/null

# MADR or adr-tools conventions
ls docs/architecture/decisions/*.md 2>/dev/null
```

For each ADR found, capture: number, title (first `#` heading), status (`Proposed` / `Accepted` / `Deprecated` / `Superseded` — look for a `Status:` line or `## Status` section), and relative path. You will **index** these — not restate them — in the Architecture Decisions section.

If no ADR directory exists, note the gap: the Architecture Decisions section will point the user to `/adr` rather than inventing decisions.

As you complete the survey (1a–1e), keep a running list of **significant decisions you can infer from the code but which have no ADR** (e.g. "chose Prisma over Drizzle", "event bus instead of direct calls", "monorepo with pnpm workspaces"). These become candidates for `/adr` in Step 3.5 — do not write their rationale into ARCHITECTURE.md.

## Step 2: Write ARCHITECTURE.md

Use this exact structure. Every section is required. If a section doesn't apply, include it with a note explaining why.

**IMPORTANT: Use the EXACT section order below. Do NOT add, remove, or reorder sections.**

```markdown
# {Project Name} — Architecture

> {One sentence: what this system does and for whom}

{Mermaid diagram showing the high-level components and how they connect.
Keep it to 5-10 boxes max — this is the 30-second orientation.}

## Testing & Verification

### Build
{build command}                [source: file:line]

### Test Suite
{test command}                 [source: file:line]
{What tests cover and what they don't}

### E2E Tests
{e2e command if applicable}    [source: file:line]
{Requirements: running server, seed data, etc. Omit section if no e2e.}

### Dev Server
{dev command}                  [source: file:line]
Port: {port}                   [source: file:line]

### How to Verify Manually
1. {step-by-step instructions for a human to verify the app works}

## Tech Stack

| Layer | Technology | Source |
|-------|-----------|--------|
| Language | {e.g. TypeScript 5.x} | `package.json:3` |
| Framework | {e.g. Next.js 14} | `package.json:5` |
| Database | {e.g. PostgreSQL via Prisma} | `prisma/schema.prisma:1` |
| Auth | {e.g. NextAuth.js} | `src/auth.config.ts:1` |
| Testing | {e.g. Vitest + Playwright} | `package.json:12` |
| Package Manager | {e.g. pnpm} | `pnpm-lock.yaml` |

## Directory Structure

{Top 2 levels with purpose annotations. Skip node_modules, .git, __pycache__.}

```
project/
├── src/               # Application source
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   ├── lib/           # Shared utilities and clients
│   └── server/        # Server-side logic
├── prisma/            # Database schema and migrations
├── tests/             # Test suites
└── scripts/           # Developer tooling
```

## Entry Points

| Trigger | Code | Purpose |
|---------|------|---------|
| `POST /api/auth/login` | `src/app/api/auth/login/route.ts:14` | Password login, returns JWT |
| `GET /api/users` | `src/app/api/users/route.ts:8` | List users (admin only) |
| CLI: `npm run seed` | `scripts/seed.ts:1` | Populate dev database |

## Module Architecture

{Mermaid diagram showing how internal modules depend on each other.
Group by layer. Dependencies should point downward.}

## Data Model

{Mermaid ERD or class diagram. 5-10 most important entities only.
3-5 fields per entity. If no database, write "No database — stateless service."}

## Key Patterns

{3-5 patterns that recur throughout the codebase. Each MUST cite a source.
This section replaces CONVENTIONS.md — include naming conventions, auth patterns,
data access patterns, error handling patterns.}

- {Pattern name}: {description} [source: file:line]
- {Pattern name}: {description} [source: file:line]

## API Surface

{Route groups for web apps, public API for libraries, commands for CLI tools.}

| Route Group | Purpose | Auth | Source |
|-------------|---------|------|--------|
| `/api/auth/*` | Authentication | Public | `src/app/api/auth/` |
| `/api/users/*` | User management | Admin | `src/app/api/users/` |

## Configuration

| Variable | Purpose | Required | Source |
|----------|---------|----------|--------|
| `DATABASE_URL` | PostgreSQL connection | Yes | `src/lib/db.ts:5` |
| `NEXTAUTH_SECRET` | Session encryption | Yes | `src/auth.config.ts:12` |

## External Dependencies

| Service | Purpose | Failure Mode |
|---------|---------|-------------|
| PostgreSQL | Primary data store | App down |
| Redis | Session cache | Degraded (falls back to DB) |

## Architecture Decisions

This section is an **index of ADRs** — rationale lives in the ADR files, not here.
Do NOT restate "why" inline. The ADR files are the authoritative source; this
section is a pointer so agents can find them.

### Recorded ADRs

| # | Title | Status | Link |
|---|-------|--------|------|
| 0001 | {Title from ADR heading} | {Accepted / Proposed / Superseded / Deprecated} | [harness-docs/adr/0001-slug.md](harness-docs/adr/0001-slug.md) |

{If no ADR files were found in Step 1f, replace the table with:

> No ADRs recorded yet. Run `/adr` to document the first decision.
> Candidate decisions surfaced during this survey: {list from Step 1f, if any}.
}

### Undocumented but observable

{For decisions inferred from code that have no ADR. One line each — no
rationale. Tell the user to run `/adr` for each before merging significant
changes that depend on them. Omit this subsection if the list is empty.}

- {Decision} [source: file:line]

## Development Workflow

```bash
# Setup
{exact commands}

# Run
{exact commands}

# Test
{exact commands}
```
```

## Step 3: Validate

After writing, verify:

1. **Every file path mentioned exists** — grep for each path you cited
2. **Every line number is accurate** — read the cited line and verify it supports the claim
3. **Every module/class/function mentioned exists** — they may have been renamed
4. **Mermaid diagrams render** — check syntax is valid
5. **Tech stack matches reality** — versions match package.json/pyproject.toml
6. **Entry points are complete** — no missing route files, CLI commands, or workers
7. **Env vars match** — cross-check with .env.example or actual config loading code

## Step 3.5: Flag ADR gaps

Before finishing, review your running list of significant decisions that have no ADR (from Step 1f). For each:

1. Confirm it is truly a decision (a choice with alternatives and trade-offs), not just a pattern.
2. Ensure ARCHITECTURE.md lists it under `### Undocumented but observable` — one line, no rationale.
3. Tell the user, explicitly, which decisions need ADRs and suggest they run `/adr` for each.

Do not create ADRs yourself from this skill. `/adr` owns ADR creation — it asks the user for context, decision, consequences, and alternatives, and writes `harness-docs/adr/NNNN-<slug>.md`. This skill only links to what `/adr` produces.

## Step 4: Done

Do NOT commit — let the user review the generated file first.

Remind the user they can run `/generate-architecture --update` in future sessions to keep the doc (and ADR index) current as the codebase evolves.

## Update Mode (--update)

When `--update` is passed:

1. Read the existing ARCHITECTURE.md
2. For each section, verify claims against current code
3. Update sections that are stale (wrong file paths, missing modules, changed patterns)
4. Preserve sections wrapped in `<!-- manual -->...<!-- /manual -->` — these were hand-written
5. Add new sections for things that didn't exist when the doc was first written
6. Remove sections for things that no longer exist
7. **Refresh the ADR index**: re-run the Step 1f scan across all ADR locations, add new ADRs to `### Recorded ADRs`, update statuses (Proposed → Accepted, Accepted → Superseded, etc.), and remove links to ADRs that were deleted. Never rewrite ADR content into ARCHITECTURE.md — only the title, status, and link.

## Rules

<rules>
<rule>Every factual claim must cite its source: endpoint paths, auth methods, config vars, patterns, entry points. Use inline format: `[source: relative/path/to/file.ext:LINE]` or put the source in a table column. If you cannot find a source for a claim, do not make the claim.</rule>
<rule>Every claim must be verified against the actual code — never guess or assume</rule>
<rule>File paths must be checked with ls or glob before writing them into the doc</rule>
<rule>Prefer showing 5 important things over listing 50 things exhaustively</rule>
<rule>Mermaid diagrams must use valid syntax — test by reading them back</rule>
<rule>The doc must be useful on day 1 to an agent with zero context — no jargon without explanation</rule>
<rule>Do not include implementation details that change frequently — focus on structure and patterns</rule>
<rule>For monorepos, show the package/app structure and how packages depend on each other</rule>
<rule>Never inline decision rationale. If a "why" needs more than one line, it belongs in an ADR file; ARCHITECTURE.md must only link to it.</rule>
<rule>The `## Architecture Decisions` section is an index of ADR links, not a place to describe decisions. If no ADRs exist, say so and point to `/adr` — do not invent entries.</rule>
<rule>If the survey surfaces a significant decision with no ADR, list it under `### Undocumented but observable` (one line, no rationale) and tell the user to run `/adr`. Do not author the rationale yourself from this skill.</rule>
</rules>

<constraints>
<constraint>Output is ARCHITECTURE.md at the repo root — one file only</constraint>
<constraint>Maximum 15 minutes — prioritize structure and patterns over exhaustive listing</constraint>
<constraint>Do not read every file — sample strategically (entry points, config, key modules)</constraint>
</constraints>
