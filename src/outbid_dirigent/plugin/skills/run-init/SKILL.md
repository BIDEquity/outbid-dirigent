---
name: run-init
description: "FALLBACK: Inspect repo and produce test-harness.json. Primary generation is via structured output from ARCHITECTURE.md. This skill is only invoked if the init script produces a harness directly."
context: fork
agent: infra-architect
---

<role>Du baust eine Test-Harness-Spezifikation mit deterministischen Commands (build, test, e2e, seed, dev), Env-Var-Metadaten und Portal-Config.</role>

<instructions>
<step id="1">Inspect the repo to understand the tech stack, dev server setup, and testing infrastructure.</step>
<step id="2">Determine the base URL and port by checking package.json scripts, docker-compose, .env files, and framework config.</step>
<step id="3">Determine how authentication works by inspecting auth routes, middleware, Playwright globalSetup, storageState config, or .env files with auth-related vars.</step>
<step id="4">Check what seed data exists — look for seed scripts, fixtures, migrations, test data files.</step>
<step id="5">Build health check commands that confirm each required service is alive.</step>
<step id="6">Build verification commands — concrete curl/CLI commands the reviewer can run to test the running system.</step>
<step id="7">Detect e2e framework (Playwright/Puppeteer/Cypress) and its run command.</step>
<step id="8">Assess testability: score 0-10 based on what's available, write rationale, description, and gaps.</step>
<step id="8b">For every value you write into the harness, record the source file and line where you found it. Store these in the `_sources` field as a flat key-value map.</step>
<step id="9">Write `${DIRIGENT_RUN_DIR}/test-harness.json` with the exact schema below.</step>
</instructions>

<discovery-hints>
<hint category="base-url">
Check these in order: .env or .env.local for PORT/BASE_URL, package.json "dev" script for --port flag, vite.config/next.config for port, docker-compose.yml for port mappings. Default: http://localhost:3000
</hint>
<hint category="auth">
Look for: /api/auth or /auth routes, NextAuth/Clerk/Supabase config, Playwright globalSetup files, storageState references in playwright.config, .env vars like JWT_SECRET/SESSION_SECRET/AUTH_*, seed scripts that create test users.
</hint>
<hint category="seed-data">
Look for: db:seed or seed scripts in package.json, prisma/seed.ts, fixtures/ directory, SQL seed files, test setup files that create users.
</hint>
<hint category="health">
Common patterns: /api/health or /health endpoint, database connection checks (pg_isready, redis-cli ping), docker-compose service health.
</hint>
<hint category="e2e">
Playwright: playwright.config.ts + "npx playwright test". Cypress: cypress.config.ts + "npx cypress run". Puppeteer: custom scripts in package.json.
</hint>
</discovery-hints>

<output file="${DIRIGENT_RUN_DIR}/test-harness.json">
{
  "base_url": "http://localhost:3000",
  "port": 3000,
  "auth": {
    "method": "bearer_token or cookie or storage_state or api_key or basic_auth or none",
    "token_env_var": "env var name if token is in env (never the actual token)",
    "login_command": "curl command that returns a token or session cookie",
    "storage_state_path": "path to Playwright storageState.json if applicable",
    "username_env_var": "",
    "password_env_var": ""
  },
  "seed": {
    "users": [
      {
        "role": "admin",
        "email": "admin@test.com",
        "password_env_var": "",
        "password_default": "test123",
        "notes": "Created by seed script"
      }
    ],
    "description": "What data exists in the system after seeding",
    "seed_command": "Command to re-run seeding (e.g. npm run db:seed)"
  },
  "health_checks": [
    {
      "name": "App server",
      "command": "curl -sf http://localhost:3000/api/health || curl -sf http://localhost:3000/",
      "timeout_seconds": 30
    }
  ],
  "e2e_framework": {
    "framework": "playwright or puppeteer or cypress or none",
    "config_file": "playwright.config.ts",
    "run_command": "npx playwright test --project=chromium",
    "has_global_setup": false,
    "global_setup_file": ""
  },
  "verification_commands": [
    {
      "name": "What this verifies",
      "command": "Runnable bash command",
      "expected": "What success looks like"
    }
  ],
  "services": ["postgres", "redis"],
  "testability_score": 7,
  "testability_rationale": "Why this score — what contributes and what detracts",
  "testability_description": "Plain text: what the test setup looks like, what the reviewer can do",
  "testability_gaps": [
    "Each gap is an actionable improvement the project could make",
    "e.g. No seed data for edge cases",
    "e.g. No e2e auth setup — reviewer can only test public endpoints"
  ],
  "status": "ready",
  "notes": "",
  "_sources": {
    "base_url": ".env:3",
    "port": "package.json:7 (dev script --port flag)",
    "auth.method": "src/app/api/auth/[...nextauth]/route.ts:1",
    "auth.login_command": "src/app/api/auth/login/route.ts:14",
    "seed.seed_command": "package.json:12 (scripts.seed)",
    "health_checks[0]": "src/app/api/health/route.ts:1",
    "verification_commands[0]": "src/app/api/users/route.ts:8"
  }
}
</output>

<testability-rubric>
<score value="0-2" label="Untestable">No dev server config, no test framework, no seed data, no health checks. Reviewer can only read code.</score>
<score value="3-4" label="Minimal">Dev server can start but no auth, no seed data, no e2e framework. Reviewer can curl public endpoints only.</score>
<score value="5-6" label="Partial">Dev server + some seed data OR auth setup, but gaps remain. Reviewer can test some flows but not all.</score>
<score value="7-8" label="Good">Dev server + auth + seed data + e2e framework configured. Reviewer can verify most features end-to-end. Minor gaps.</score>
<score value="9-10" label="Excellent">Full stack running, auth works, rich seed data, e2e suite passes, health checks green, API contracts validated. Reviewer can verify everything.</score>
</testability-rubric>

<rules>
<rule>The output MUST be valid JSON matching the schema exactly</rule>
<rule>NEVER include actual passwords, tokens, or secrets — only env var names or known test defaults</rule>
<rule>Every verification_command must be a concrete, runnable bash command (not pseudocode)</rule>
<rule>Every health_check command must exit 0 when healthy, non-zero when not</rule>
<rule>If you can't determine something, use sensible defaults and note it in "notes"</rule>
<rule>The login_command must be a complete curl command the reviewer can copy-paste</rule>
<rule>If no auth is needed (public API), set method to "none"</rule>
<rule>If a prior test-harness.json exists, read it for context on previous init runs</rule>
<rule>Every harness value must have a corresponding entry in `_sources` citing the file:line where the claim originates. If you cannot find a source, set the value to empty string and note the gap in `_sources` as "NOT_FOUND: searched X, Y, Z".</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>The file path MUST be ${DIRIGENT_RUN_DIR}/test-harness.json</constraint>
</constraints>

## Validation (MANDATORY)

After writing test-harness.json, validate it:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/validate_schema.py ${DIRIGENT_RUN_DIR}/test-harness.json
```

If validation fails, fix the errors and re-run until it passes.
