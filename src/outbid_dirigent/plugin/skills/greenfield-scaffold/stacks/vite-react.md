# Vite + React

**Role:** JS Frontend — SPAs, interactive UIs, form-heavy apps
**Tier:** 1 (default for JS frontend)
**When:** SPEC needs an interactive web UI without server-side rendering

## Docs

Before using unfamiliar Vite or React APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="vite"` (or `"react"`) → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
node --version   # >= 18
npm --version
```

## Scaffold

```bash
npm create vite@latest . -- --template react-ts
npm install
```

Flags: fully non-interactive, zero prompts, produces clean `src/main.tsx`.

## Run

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

Port: **5173** (default)

## Test

Scaffold does NOT include test setup. Add Vitest:

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

Add to `vite.config.ts`:

```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.ts',
  },
})
```

```typescript
// src/test-setup.ts
import '@testing-library/jest-dom'
```

```typescript
// src/App.test.tsx
import { render, screen } from '@testing-library/react'
import App from './App'

test('renders app', () => {
  render(<App />)
  expect(document.body).toBeTruthy()
})
```

```bash
npx vitest run
```

## E2E (Playwright) — MANDATORY for web archetypes

Install Playwright **unconditionally** during scaffold. The install command below is stable and does NOT require a context7 lookup — do not skip this step just because context7 is unavailable.

```bash
npm install -D @playwright/test
npx playwright install --with-deps chromium
npx playwright install chromium   # fallback if --with-deps needs sudo
```

Minimal config (`playwright.config.ts` — committed):

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'tests/e2e',
  use: { baseURL: 'http://localhost:5173' },
  webServer: {
    command: 'npm run dev -- --host 0.0.0.0 --port 5173',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
```

First smoke spec (`tests/e2e/smoke.spec.ts`):

```typescript
import { test, expect } from '@playwright/test'

test('app renders', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('#root')).toBeVisible()
})
```

Run:

```bash
npx playwright test
```

Write `e2e_framework` into `test-harness.json`:

```json
"e2e_framework": {
  "name": "playwright",
  "run_command": "npx playwright test"
}
```

**Use context7 only if** you need to look up a specific matcher or assertion API while writing the first spec — query `mcp__context7__query-docs` with `libraryName="playwright"`. Missing context7 is NOT a reason to skip install or scaffold.

## Build & Verify

```bash
npm run build   # produces dist/
npx serve dist  # verify production build
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
npm install
exec npm run dev -- --host 0.0.0.0 --port 5173
```

## Pairing

- **+ FastAPI** → React SPA + Python API (proxy in vite.config.ts)
- **+ PocketBase** → React SPA + instant backend (pocketbase-js SDK)
- **+ Supabase Local** → React SPA + Postgres backend (@supabase/supabase-js)
