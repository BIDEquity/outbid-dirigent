---
name: generate-architecture
description: Generate ARCHITECTURE.md for the target repository — a complete, agent-readable map of the codebase
context: fork
agent: infra-architect
---

# Generate Architecture

You produce `ARCHITECTURE.md` — a single file that gives any agent (or human) landing in this repo everything it needs to navigate and modify the codebase confidently.

## Why This Matters

Without an architecture doc, every agent session starts with 10-15 minutes of codebase exploration. Worse, agents make wrong assumptions about how modules connect, where data flows, and what patterns to follow. ARCHITECTURE.md eliminates this cold-start penalty.

This is NOT documentation for documentation's sake. Every section exists because an agent will need it to make better decisions.

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

## Step 2: Write ARCHITECTURE.md

Use this exact structure. Every section is required. If a section doesn't apply, include it with a note explaining why.

**IMPORTANT: Use the EXACT section order and XML tags below. Do NOT add, remove, or reorder sections.**

```markdown
# {Project Name} — Architecture

<system-overview>
> {One sentence: what this system does and for whom}

{Mermaid diagram showing the high-level components and how they connect.
Keep it to 5-10 boxes max — this is the 30-second orientation.}
</system-overview>

<testing-verification>
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
</testing-verification>

<tech-stack>
## Tech Stack

| Layer | Technology | Source |
|-------|-----------|--------|
| Language | {e.g. TypeScript 5.x} | `package.json:3` |
| Framework | {e.g. Next.js 14} | `package.json:5` |
| Database | {e.g. PostgreSQL via Prisma} | `prisma/schema.prisma:1` |
| Auth | {e.g. NextAuth.js} | `src/auth.config.ts:1` |
| Testing | {e.g. Vitest + Playwright} | `package.json:12` |
| Package Manager | {e.g. pnpm} | `pnpm-lock.yaml` |
</tech-stack>

<directory-structure>
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
</directory-structure>

<entry-points>
## Entry Points

| Trigger | Code | Purpose |
|---------|------|---------|
| `POST /api/auth/login` | `src/app/api/auth/login/route.ts:14` | Password login, returns JWT |
| `GET /api/users` | `src/app/api/users/route.ts:8` | List users (admin only) |
| CLI: `npm run seed` | `scripts/seed.ts:1` | Populate dev database |
</entry-points>

<module-architecture>
## Module Architecture

{Mermaid diagram showing how internal modules depend on each other.
Group by layer. Dependencies should point downward.}
</module-architecture>

<data-model>
## Data Model

{Mermaid ERD or class diagram. 5-10 most important entities only.
3-5 fields per entity. If no database, write "No database — stateless service."}
</data-model>

<key-patterns>
## Key Patterns

{3-5 patterns that recur throughout the codebase. Each MUST cite a source.
This section replaces CONVENTIONS.md — include naming conventions, auth patterns,
data access patterns, error handling patterns.}

- {Pattern name}: {description} [source: file:line]
- {Pattern name}: {description} [source: file:line]
</key-patterns>

<api-surface>
## API Surface

{Route groups for web apps, public API for libraries, commands for CLI tools.}

| Route Group | Purpose | Auth | Source |
|-------------|---------|------|--------|
| `/api/auth/*` | Authentication | Public | `src/app/api/auth/` |
| `/api/users/*` | User management | Admin | `src/app/api/users/` |
</api-surface>

<configuration>
## Configuration

| Variable | Purpose | Required | Source |
|----------|---------|----------|--------|
| `DATABASE_URL` | PostgreSQL connection | Yes | `src/lib/db.ts:5` |
| `NEXTAUTH_SECRET` | Session encryption | Yes | `src/auth.config.ts:12` |
</configuration>

<external-dependencies>
## External Dependencies

| Service | Purpose | Failure Mode |
|---------|---------|-------------|
| PostgreSQL | Primary data store | App down |
| Redis | Session cache | Degraded (falls back to DB) |
</external-dependencies>

<architecture-decisions>
## Architecture Decisions

{Key design decisions and their rationale. For greenfield projects, document
choices made during scaffold. For existing projects, document discovered patterns.
If none, write "No notable architecture decisions documented."}

- {Decision}: {rationale} [source: file:line]
</architecture-decisions>

<development-workflow>
## Development Workflow

```bash
# Setup
{exact commands}

# Run
{exact commands}

# Test
{exact commands}
```
</development-workflow>
```

## Step 3: Validate

After writing, verify:

1. **Every file path mentioned exists** — grep for each path you cited
2. **Every line number is accurate** — read the cited line and verify it supports the claim
3. **Every module/class/function mentioned exists** — they may have been renamed
3. **Mermaid diagrams render** — check syntax is valid
4. **Tech stack matches reality** — versions match package.json/pyproject.toml
5. **Entry points are complete** — no missing route files, CLI commands, or workers
6. **Env vars match** — cross-check with .env.example or actual config loading code

## Step 4: Commit (if in Dirigent pipeline)

If running as part of the Dirigent pipeline:
```bash
git add ARCHITECTURE.md && git commit -m "docs: generate ARCHITECTURE.md"
```

If running standalone (user invoked directly), do NOT commit — let the user review first.

## Update Mode (--update)

When `--update` is passed:

1. Read the existing ARCHITECTURE.md
2. For each section, verify claims against current code
3. Update sections that are stale (wrong file paths, missing modules, changed patterns)
4. Preserve sections wrapped in `<!-- manual -->...<!-- /manual -->` — these were hand-written
5. Add new sections for things that didn't exist when the doc was first written
6. Remove sections for things that no longer exist
7. Commit: `git add ARCHITECTURE.md && git commit -m "docs: update ARCHITECTURE.md"`

## Rules

<rules>
<rule>Every factual claim must cite its source: endpoint paths, auth methods, config vars, patterns, entry points. Use inline format: `[source: relative/path/to/file.ext:LINE]` or put the source in a table column. If you cannot find a source for a claim, do not make the claim.</rule>
<rule>Every claim must be verified against the actual code — never guess or assume</rule>
<rule>File paths must be checked with ls or glob before writing them into the doc</rule>
<rule>Prefer showing 5 important things over listing 50 things exhaustively</rule>
<rule>Mermaid diagrams must use valid syntax — test by reading them back</rule>
<rule>The doc must be useful on day 1 to an agent with zero context — no jargon without explanation</rule>
<rule>If running as part of Dirigent init, always commit. If standalone, never commit.</rule>
<rule>Do not include implementation details that change frequently — focus on structure and patterns</rule>
<rule>For monorepos, show the package/app structure and how packages depend on each other</rule>
</rules>

<constraints>
<constraint>Output is ARCHITECTURE.md at the repo root — one file only</constraint>
<constraint>Maximum 15 minutes — prioritize structure and patterns over exhaustive listing</constraint>
<constraint>Do not read every file — sample strategically (entry points, config, key modules)</constraint>
</constraints>
