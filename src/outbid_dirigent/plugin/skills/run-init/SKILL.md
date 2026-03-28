---
name: run-init
description: Run init script to bootstrap dev environment, seed data, and configure e2e test credentials
arguments: none - repo path determined automatically
---

# Run Init Script

Bootstrap the development environment before planning begins.

## Purpose

Before any planning or execution, the init phase:
1. Starts required services (databases, APIs, etc.)
2. Seeds development data
3. Configures credentials for Playwright/Puppeteer e2e testing
4. Validates the environment is ready for development

## Init Script Discovery

Look for init scripts in this order:
1. `.outbid/init.sh` — Outbid-specific init script
2. `init.sh` — Generic init script in repo root

## Process

### Step 1: Find and Read the Init Script

```bash
# Check for init scripts
if [ -f ".outbid/init.sh" ]; then
  INIT_SCRIPT=".outbid/init.sh"
elif [ -f "init.sh" ]; then
  INIT_SCRIPT="init.sh"
else
  echo "No init script found — skipping init phase"
  exit 0
fi
```

### Step 2: Execute the Init Script

```bash
chmod +x "$INIT_SCRIPT"
bash "$INIT_SCRIPT" 2>&1 | tee .dirigent/init-output.log
```

### Step 3: Capture Environment

After the init script runs, capture the environment state:

```bash
# Capture any exported env vars (especially for e2e testing)
env | grep -iE '(PLAYWRIGHT|PUPPETEER|BROWSER|E2E|TEST_URL|BASE_URL|COOKIE|TOKEN|SESSION|AUTH|CREDENTIAL|HEADLESS)' > .dirigent/init-env.txt 2>/dev/null || true
```

### Step 4: Validate Readiness

Check that the environment is ready:

```bash
# Check if common services are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true

# Check if dev server ports are in use
for port in 3000 3001 4000 5000 5173 8000 8080; do
  if ss -tlnp 2>/dev/null | grep -q ":$port "; then
    echo "Port $port: LISTENING"
  fi
done
```

### Step 5: Write Init Report

Create `.dirigent/INIT_REPORT.md`:

```markdown
# Init Report

## Script Used
{path to init script}

## Services Started
{list of services/containers started}

## Ports Listening
{list of active ports}

## E2E Test Configuration
- Base URL: {detected base URL}
- Browser: {Playwright/Puppeteer/none}
- Auth Method: {how e2e tests authenticate}
- Credentials: {reference to env vars, NOT actual values}

## Seeded Data
{what data was seeded, if any}

## Environment Variables Set
{list of relevant env vars, values redacted}

## Status: READY | PARTIAL | FAILED
{overall readiness assessment}
```

## E2E Credential Handling

The init script is expected to handle e2e credentials in one of these ways:

1. **Environment variables**: Export `PLAYWRIGHT_*` or `E2E_*` vars
2. **Auth state file**: Create a Playwright `storageState.json` or similar
3. **Config file**: Write to `playwright.config.ts` or `e2e/config.ts`
4. **Service account**: Start a test user session and save the token

The init report captures WHICH method is used so the planner can reference it.

## Constraints

- NEVER log actual passwords or tokens — only reference env var names
- If the init script fails, log the error but don't block (set status to PARTIAL)
- Timeout after 5 minutes — init scripts that hang are likely misconfigured
- If no init script exists, create a minimal `.dirigent/INIT_REPORT.md` noting no init was needed
