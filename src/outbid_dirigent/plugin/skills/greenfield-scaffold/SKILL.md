---
name: greenfield-scaffold
description: For greenfield projects, propose a test setup and architecture best practices before planning. Writes testing-verification, architecture-decisions, and key-patterns sections into ARCHITECTURE.md.
context: fork
agent: infra-architect
---

# Greenfield Scaffold

You analyze a greenfield project and write the `<testing-verification>`, `<architecture-decisions>`, and `<key-patterns>` sections of ARCHITECTURE.md. These sections guide every downstream task — the planner, executor, and reviewer all read them.

Get them right and the entire feature ships clean. Get them wrong and every task fights the architecture.

## When This Runs

After init (test harness exists), before planning. You have:
- `${DIRIGENT_RUN_DIR}/SPEC.md` — what's being built
- `${DIRIGENT_RUN_DIR}/ANALYSIS.json` — repo structure, language, framework
- `${DIRIGENT_RUN_DIR}/test-harness.json` — available infra (services, auth, seed data)
- `ARCHITECTURE.md` — system overview (if generated during init)
- The live repo — read whatever you need

## Step 1: Assess What Exists

Before proposing anything, understand what's already in place.

```bash
# What test infrastructure exists?
ls jest.config* vitest.config* pytest.ini pyproject.toml conftest.py .rspec Gemfile 2>/dev/null
ls -d test/ tests/ spec/ __tests__/ e2e/ cypress/ playwright/ 2>/dev/null

# What test runner is configured?
grep -r "jest\|vitest\|pytest\|rspec\|mocha\|playwright\|cypress" package.json pyproject.toml Gemfile 2>/dev/null

# What patterns are already established?
ls test/**/*.test.* tests/**/*.py spec/**/*_spec.rb 2>/dev/null | head -10

# What CI exists?
ls .github/workflows/*.yml .gitlab-ci.yml Jenkinsfile .circleci/config.yml 2>/dev/null
```

If `.brv/context-tree/` exists and `brv` CLI is available, query for existing architectural decisions:
```bash
brv query "What architecture patterns, testing strategies, and design decisions exist?"
```
Incorporate any relevant BRV knowledge into your strategy — don't propose patterns that contradict curated decisions.

Read `${DIRIGENT_RUN_DIR}/ANALYSIS.json` for detected language, framework, and test infrastructure.
Read `${DIRIGENT_RUN_DIR}/test-harness.json` for available services and testability score.
Read `${DIRIGENT_RUN_DIR}/SPEC.md` for feature requirements.

## Step 2: Decide Test Strategy

Choose the right testing approach based on what you found. Not every project needs every layer.

### Decision Framework

| Signal | Strategy |
|--------|----------|
| API/backend project, services available | **Integration-heavy**: real DB, real HTTP, minimal mocking |
| Frontend SPA, no backend in scope | **Component-heavy**: component tests + visual snapshots |
| Full-stack feature, e2e framework detected | **E2E-anchored**: e2e happy paths + unit for logic |
| Library/utility, no services | **Unit-heavy**: pure function tests, edge cases |
| CLI tool | **Snapshot + integration**: golden file tests, subprocess tests |

### Test Layers (pick what applies)

**Layer 1 — Static analysis** (always)
- Type checking (TypeScript strict, mypy, pyright)
- Linting (ESLint, ruff, rubocop)
- Cost: zero runtime, catches ~30% of bugs

**Layer 2 — Unit tests** (when there's logic)
- Pure functions, transformations, validators, business rules
- No I/O, no network, no database
- Framework: match what's already in the project, or:
  - TypeScript → Vitest (fast, ESM-native)
  - Python → pytest (fixtures, parametrize)
  - Ruby → Minitest or RSpec (match existing)
  - Go → stdlib testing
  - Rust → built-in #[test]

**Layer 3 — Integration tests** (when there's a database or API)
- Real database (not SQLite-in-memory unless prod uses SQLite)
- Real HTTP requests to running server
- Factory/fixture pattern for test data
- Framework: same as unit, but with test DB setup/teardown

**Layer 4 — E2E tests** (when there's a UI or multi-service flow)
- Only for critical user journeys (3-5 scenarios max)
- Framework: Playwright (preferred), Cypress (if already in project)
- Test against running dev server
- Store auth state to avoid login in every test

### Anti-Patterns to Avoid

- **Mocking what you own**: Don't mock your own database or services. Mock external APIs only.
- **Testing implementation**: Test behavior ("user sees error message"), not implementation ("function throws at line 42").
- **100% coverage goals**: Coverage is a byproduct, not a target. 80% meaningful coverage > 100% with `/* istanbul ignore */`.
- **Slow test suites**: If tests take > 30s locally, developers won't run them. Parallelize or split.
- **Snapshot abuse**: Snapshots for large objects/HTML rot fast. Use them for small, stable structures only.

## Step 3: Decide Architecture Patterns

For greenfield features, establish patterns BEFORE coding starts. The first file sets the precedent.

### Decision Framework

Read the spec and decide which patterns apply. Only propose patterns the feature actually needs.

**API Design:**

| Signal | Pattern |
|--------|---------|
| CRUD-heavy, resource-oriented | REST with consistent URL scheme (`/api/v1/{resource}`) |
| Complex queries, multiple consumers | GraphQL with schema-first design |
| Internal service, simple contract | RPC-style (tRPC, gRPC, or plain functions) |

**Data Access:**

| Signal | Pattern |
|--------|---------|
| Complex queries, multiple models | Repository pattern (DB logic in dedicated classes) |
| Simple CRUD, one model per route | Direct ORM in route handlers (simpler) |
| Multiple data sources | Service layer between routes and data |

**Error Handling:**

| Signal | Pattern |
|--------|---------|
| API with consumers | Typed error responses with error codes (`{ error: "NOT_FOUND", message: "..." }`) |
| Internal tool | Exceptions with context (no catch-all) |
| Multi-step pipeline | Result type (`Ok/Err` or `{success, data, error}`) |

**State Management (frontend):**

| Signal | Pattern |
|--------|---------|
| Server state (API data) | React Query / SWR / TanStack Query (cache + revalidation) |
| Client state (UI state) | Local component state or context (no Redux for small apps) |
| Complex forms | React Hook Form or Formik |

**File Organization:**

| Signal | Pattern |
|--------|---------|
| Feature-scoped work | Feature folders (`features/auth/`, `features/dashboard/`) |
| Shared utilities, libraries | Layer folders (`lib/`, `utils/`, `services/`) |
| Monorepo with multiple apps | Package-per-app with shared packages |

### Principles (always apply)

1. **Explicit dependencies** — pass them in, don't import globals. Makes testing trivial.
2. **One file, one concept** — a file should be about one thing. If you need a comment header to separate sections, split the file.
3. **Errors at boundaries** — validate at the edge (API handler, CLI parser). Internal code trusts the types.
4. **Configuration as data** — env vars → typed config object at startup. No `process.env.X` scattered through business logic.
5. **Naming is documentation** — `getUserById(id)` needs no JSDoc. `process(data)` needs a rewrite.

## Step 4: Write Into ARCHITECTURE.md

Read the existing ARCHITECTURE.md (generated during init). Update these three sections with your findings. Preserve all other sections unchanged.

### Section: `<testing-verification>`

Replace the placeholder content with your concrete strategy:

```markdown
<testing-verification>
## Testing & Verification

### Build
{build command}                [source: package.json:X]

### Test Suite
{test command}                 [source: package.json:X]
Framework: {Vitest/pytest/etc.} — {why this one}
Location: {test directory pattern}
Covers: {what gets tested}
Does NOT cover: {what's excluded and why}

### E2E Tests
{e2e command if applicable}    [source: playwright.config.ts:X]
Framework: {Playwright/Cypress} — {why}
Requires: {running server, seed data, etc.}

### Seed Data
{seed command}                 [source: package.json:X]
Strategy: {factories / fixtures / seed script}
Database: {real DB / SQLite-in-memory / etc.}

### Dev Server
{dev command}                  [source: package.json:X]
Port: {port}                   [source: .env:X]

### How to Verify Manually
1. {step-by-step for a human}
</testing-verification>
```

### Section: `<architecture-decisions>`

```markdown
<architecture-decisions>
## Architecture Decisions

### {Pattern Name} (e.g. "Repository Pattern for Data Access")
- **When to use**: {trigger condition}
- **Rationale**: {why}
- **Structure**: {3-8 line code skeleton}

### Project Bootstrap
Scaffold command: `{e.g. npx create-next-app@latest . --ts --tailwind --app}`

### File Organization
```
{proposed directory tree, 10-15 lines}
```

### Dependencies to Add
| Package | Purpose | Why this one |
|---------|---------|-------------|
| {pkg} | {what} | {why not alternatives} |

### Decisions NOT Made
{What's deliberately left open and why}
</architecture-decisions>
```

### Section: `<key-patterns>`

```markdown
<key-patterns>
## Key Patterns

- {Naming}: {convention} [source: file:line or "scaffold decision"]
- {Error handling}: {pattern} [source: file:line or "scaffold decision"]
- {Config access}: {pattern} [source: file:line or "scaffold decision"]
- {Exports}: {convention} [source: file:line or "scaffold decision"]
</key-patterns>
```

## Step 5: Scaffold Command

For greenfield projects, the architecture-decisions.md MUST include a **scaffold command** that the planner's first task will execute. Do NOT plan to create project files manually — use the framework's official scaffolder:

| Framework | Scaffold Command |
|-----------|-----------------|
| Next.js | `npx create-next-app@latest . --ts --tailwind --eslint --app --src-dir --no-git --yes` |
| Vite (React) | `npm create vite@latest . -- --template react-ts` |
| Nuxt | `npx nuxi init . --no-git` |
| SvelteKit | `npx sv create . --template minimal --types ts` |
| Remix | `npx create-remix@latest . --no-git-init` |
| Django | `django-admin startproject config .` |
| FastAPI | manual (no official scaffolder — document minimal file structure) |
| Rails | `rails new . --skip-git` |
| Go | `go mod init {module}` |
| Rust | `cargo init .` |
| Flutter | `flutter create .` |

**Why:** Scaffolders generate config files (e.g. `next.config.mjs`, `vite.config.ts`) that match the installed framework version. Writing these files manually leads to version mismatches — e.g. creating `next.config.ts` when the installed Next.js only supports `.js` or `.mjs`.

If the repo already has a `package.json` or framework config, skip scaffolding and work with what exists.

Include the chosen scaffold command in architecture-decisions.md under a `## Project Bootstrap` section so the planner puts it as the very first task.

## Step 6: Validate

Before writing:

1. **Every tool/framework suggested must be compatible** with the detected stack (don't suggest Vitest for a Python project)
2. **Every command must work** — verify by checking package.json scripts, Makefile targets, etc.
3. **Every pattern must be justified** by the spec requirements — don't propose Repository pattern for a 2-endpoint feature
4. **Keep it proportional** — a small feature needs 1 page, not 10. Scale recommendations to scope.

## Step 7: Commit

```bash
git add ARCHITECTURE.md
git commit -m "docs: greenfield scaffold — testing strategy, architecture decisions, key patterns"
```

## Rules

<rules>
<rule>Match recommendations to project scale — a weekend project doesn't need the same architecture as a SaaS platform</rule>
<rule>Every recommendation must have a concrete reason tied to the spec — no "best practice for best practice's sake"</rule>
<rule>Prefer the tools already in the project over introducing new ones</rule>
<rule>If the project has existing patterns (even partial), extend them instead of replacing</rule>
<rule>Test strategy must be executable — commands, not concepts. "Run pytest" not "ensure adequate coverage"</rule>
<rule>Architecture patterns must include code skeletons — show the shape, not just the name</rule>
<rule>Do not over-engineer — if the spec describes 3 endpoints, don't propose a microservice architecture</rule>
<rule>NEVER plan to write framework config files manually (next.config.*, vite.config.*, etc.) — always use the official scaffolder which generates version-correct configs</rule>
<rule>Acknowledge what you don't know — if a decision depends on requirements not in the spec, say so in "Decisions NOT Made"</rule>
</rules>

<constraints>
<constraint>Output: Update <testing-verification>, <architecture-decisions>, and <key-patterns> sections in ARCHITECTURE.md</constraint>
<constraint>Maximum 15 minutes</constraint>
<constraint>Both artifacts combined should be under 300 lines — these get consumed by the planner, not published as docs</constraint>
</constraints>
