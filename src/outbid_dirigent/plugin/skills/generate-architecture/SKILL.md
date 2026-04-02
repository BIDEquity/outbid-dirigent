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

```markdown
# {Project Name} — Architecture

> {One sentence: what this system does and for whom}

## System Overview

{Mermaid diagram showing the high-level components and how they connect.
For web apps: client → API → services → database.
For CLI tools: input → processing pipeline → output.
For libraries: public API → internal modules.
Keep it to 5-10 boxes max — this is the 30-second orientation.}

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | {e.g. TypeScript 5.x} | |
| Framework | {e.g. Next.js 14 (App Router)} | |
| Database | {e.g. PostgreSQL via Prisma} | |
| Cache | {e.g. Redis} | {if applicable} |
| Auth | {e.g. NextAuth.js / Clerk / custom JWT} | |
| Testing | {e.g. Vitest + Playwright} | |
| Deployment | {e.g. Vercel / Docker / AWS} | |
| Package Manager | {e.g. pnpm / uv / cargo} | |

## Directory Structure

{Show the top 2 levels of meaningful directories. Annotate each with its purpose.
Skip node_modules, .git, __pycache__, etc.}

```
project/
├── src/               # Application source
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   ├── lib/           # Shared utilities and clients
│   └── server/        # Server-side logic (API routes, services)
├── prisma/            # Database schema and migrations
├── tests/             # Test suites
└── scripts/           # Developer tooling
```

## Entry Points

{List every way execution enters the system. For each, state:
- What triggers it (HTTP request, CLI command, cron, queue message)
- Where the code lives (file path)
- What it does in one sentence}

## Module Architecture

{Mermaid diagram showing how internal modules depend on each other.
Group by layer (API/Routes → Services/Business Logic → Data/Infrastructure).
Show the direction of dependencies — dependencies should point downward.}

## Data Model

{If the project has a database, show the key entities and their relationships.
Use a mermaid ERD or class diagram. Only include the 5-10 most important entities.
For each entity, list the 3-5 most important fields, not every column.}

## Key Patterns

{Describe 3-5 patterns that recur throughout the codebase. For each:
- Name the pattern
- Show one concrete example (file path + brief code reference)
- Explain when to use it (so the agent follows the pattern for new code)}

Example patterns:
- "All API routes use the `withAuth` middleware for authentication"
- "Database queries go through repository classes, never direct Prisma calls in routes"
- "Background jobs extend the `BaseJob` class and are registered in `jobs/index.ts`"

## API Surface

{For web apps: list the main API route groups with their purpose.
For libraries: list the public API functions/classes.
For CLI tools: list the commands and subcommands.
Don't list every endpoint — group them.}

| Route Group | Purpose | Auth |
|-------------|---------|------|
| `/api/auth/*` | Authentication (login, register, session) | Public |
| `/api/users/*` | User management | Admin |
| `/api/projects/*` | Project CRUD and collaboration | User |

## Configuration

{Where config lives, what env vars are required, and how config flows into the app.}

| Variable | Purpose | Required |
|----------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `NEXTAUTH_SECRET` | Session encryption key | Yes |

## External Dependencies

{Services this system talks to. For each: what, why, and what happens if it's down.}

| Service | Purpose | Failure Mode |
|---------|---------|-------------|
| PostgreSQL | Primary data store | App down |
| Redis | Session cache, rate limiting | Degraded (falls back to DB) |
| Stripe | Payment processing | Payments fail, app continues |

## Development Workflow

{How to go from a fresh clone to a running system. Be specific — exact commands.}

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
2. **Every module/class/function mentioned exists** — they may have been renamed
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
