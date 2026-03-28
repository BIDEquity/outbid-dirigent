---
name: run-init
description: Run init script to bootstrap dev environment, seed data, and configure e2e credentials
---

# Run Init Script

Bootstrap the development environment before planning.

## Step 1: Find Init Script

```bash
if [ -f ".outbid/init.sh" ]; then
  INIT_SCRIPT=".outbid/init.sh"
elif [ -f "init.sh" ]; then
  INIT_SCRIPT="init.sh"
else
  echo "No init script found"
fi
```

If no script found, write a minimal `.dirigent/INIT_REPORT.md` noting no init was needed and exit.

## Step 2: Execute

```bash
chmod +x "$INIT_SCRIPT"
bash "$INIT_SCRIPT" 2>&1 | tee .dirigent/init-output.log
```

## Step 3: Capture Environment

```bash
# E2e-relevant env vars (names only, never values)
env | grep -iE '(PLAYWRIGHT|PUPPETEER|BROWSER|E2E|TEST_URL|BASE_URL|TOKEN|SESSION|AUTH|HEADLESS)' | cut -d= -f1 > .dirigent/init-env.txt 2>/dev/null || true

# Docker services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || true

# Listening ports
for port in 3000 3001 4000 5000 5173 8000 8080; do
  ss -tlnp 2>/dev/null | grep -q ":$port " && echo "Port $port: LISTENING"
done
```

## Step 4: Write Report

Create `.dirigent/INIT_REPORT.md`:

```markdown
# Init Report

## Script Used
{path}

## Services Started
{list}

## Ports Listening
{list}

## E2E Test Configuration
- Base URL: {detected}
- Framework: {Playwright/Puppeteer/Cypress/none}
- Auth Method: {how e2e tests authenticate}
- Credentials: {env var names only, NEVER actual values}

## Status: READY | PARTIAL | FAILED
```

## Constraints

- NEVER log actual passwords or tokens
- Timeout after 5 minutes
- If script fails, set status to PARTIAL (don't block)
