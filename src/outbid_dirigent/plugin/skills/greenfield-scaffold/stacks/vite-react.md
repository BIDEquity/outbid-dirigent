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

## Stock Landing Replacement

Immediately after `npm create vite`, overwrite `src/App.tsx` (and drop the Vite/React logo assets). The stock file has "Vite + React", a counter, and links to the framework docs — it MUST go before the first real phase starts.

Minimal template (adjust the heading to the SPEC's working title; `router` choice is out of scope — use whatever routing lib the SPEC implies, or a plain anchor for now):

```tsx
// src/App.tsx
export default function App() {
  return (
    <main
      style={{
        maxWidth: 560,
        margin: '0 auto',
        padding: '64px 24px',
        textAlign: 'center',
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: '-0.01em' }}>
        {APP_TITLE}
      </h1>
      <p style={{ color: '#52525b', fontSize: 14, marginTop: 8 }}>
        {ONE_LINE_DESCRIPTION_FROM_SPEC}
      </p>
      <a
        href="/login"
        style={{
          display: 'inline-block',
          marginTop: 24,
          padding: '10px 16px',
          borderRadius: 6,
          background: '#18181b',
          color: '#fff',
          fontSize: 14,
          textDecoration: 'none',
        }}
      >
        Sign in
      </a>
    </main>
  )
}
```

Also delete `src/App.css`, `src/assets/react.svg`, and `public/vite.svg` if they exist — the template above uses inline styles only.

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

## Dev Credentials Banner

Add a component that renders the test credentials only in dev:

```tsx
// src/components/DevCredentialsBanner.tsx
export function DevCredentialsBanner() {
  if (!import.meta.env.DEV) return null
  return (
    <div
      role="note"
      style={{
        borderBottom: '1px solid #fcd34d',
        background: '#fffbeb',
        color: '#78350f',
        padding: '8px 16px',
        fontSize: 12,
      }}
    >
      <strong>Dev mode test login:</strong>{' '}
      <code>admin@test.local</code> / <code>testpass123</code>
      {' '}— seeded by the backend. Never rendered in production.
    </div>
  )
}
```

Mount it at the top of `src/App.tsx` (or your root component), before the main content.

README.md `## Local Development` section — copy verbatim:

```markdown
## Local Development

Test login (seeded automatically on first run):

- Email: `admin@test.local`
- Password: `testpass123`

Credentials also shown as a dev-mode banner at the top of the app; banner is stripped from production builds (`import.meta.env.DEV`).
```

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

PORT="${PORT:-5173}"

npm install

cat <<BANNER
──────────────────────────────────────────
  App URL        : http://localhost:${PORT}
  Test login     : admin@test.local / testpass123
                   (seeded by backend; dev-mode banner on every page)
  Override port  : PORT=4000 ./start.sh
──────────────────────────────────────────
BANNER

exec npm run dev -- --host 0.0.0.0 --port "$PORT"
```

## Pairing

- **+ FastAPI** → React SPA + Python API (proxy in vite.config.ts)
- **+ PocketBase** → React SPA + instant backend (pocketbase-js SDK)
- **+ Supabase Local** → React SPA + Postgres backend (@supabase/supabase-js)
