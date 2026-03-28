---
name: run-init
description: Inspect repo and produce a test harness specification for e2e verification
---

<role>Du baust eine Test-Harness-Spezifikation die dem Reviewer sagt wie er Features end-to-end verifizieren kann.</role>

<instructions>
<step id="1">Inspect the repo to understand the tech stack, dev server setup, and testing infrastructure.</step>
<step id="2">Determine the base URL and port by checking package.json scripts, docker-compose, .env files, and framework config.</step>
<step id="3">Determine how authentication works by inspecting auth routes, middleware, Playwright globalSetup, storageState config, or .env files with auth-related vars.</step>
<step id="4">Check what seed data exists — look for seed scripts, fixtures, migrations, test data files.</step>
<step id="5">Build health check commands that confirm each required service is alive.</step>
<step id="6">Build verification commands — concrete curl/CLI commands the reviewer can run to test the running system.</step>
<step id="7">Detect e2e framework (Playwright/Puppeteer/Cypress) and its run command.</step>
<step id="8">Assess testability: score 0-10 based on what's available, write rationale, description, and gaps.</step>
<step id="9">Write `.dirigent/test-harness.json` with the exact schema below.</step>
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

<output file=".dirigent/test-harness.json">
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
  "notes": ""
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
<rule>If .dirigent/init-output.log exists, read it for clues about what init.sh did</rule>
<rule>If .dirigent/init-new-env.json exists, read it for env vars the init script exported</rule>
</rules>

<constraints>
<constraint>Output ONLY the JSON file — no markdown, no commentary</constraint>
<constraint>The file path MUST be .dirigent/test-harness.json</constraint>
</constraints>
