# Next.js

**Role:** Full-stack JS — frontend + API routes in one project
**Tier:** 1 (default for full-stack JS)
**When:** SPEC needs both a web UI and API endpoints in one codebase

## Docs

Before using unfamiliar Next.js APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="nextjs"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
node --version   # >= 18
npm --version
npx --version
```

## Scaffold

```bash
npx create-next-app@latest . --yes --typescript --tailwind --eslint --app --src-dir --no-git
npm install
```

Flags: `--yes` makes it fully non-interactive. `--no-git` avoids nested `.git`.

**CRITICAL:** Never write `next.config.*` manually — the scaffold generates the version-correct config.

## Run

```bash
npm run dev -- -H 0.0.0.0 -p 3000
```

Port: **3000** (default)

## Test

Scaffold does NOT include test setup. Add Vitest:

```bash
npm install -D vitest @vitejs/plugin-react @testing-library/react @testing-library/jest-dom jsdom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'
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
// src/app/page.test.tsx
import { render } from '@testing-library/react'
import Page from './page'

test('renders home page', () => {
  const { container } = render(<Page />)
  expect(container).toBeTruthy()
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
  use: { baseURL: 'http://localhost:3000' },
  webServer: {
    command: 'npm run dev -- -H 0.0.0.0 -p 3000',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
```

First smoke spec (`tests/e2e/smoke.spec.ts`):

```typescript
import { test, expect } from '@playwright/test'

test('home page renders', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('body')).toBeVisible()
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

Add a server component that renders the test credentials in dev builds and disappears in production:

```tsx
// src/components/DevCredentialsBanner.tsx
export function DevCredentialsBanner() {
  if (process.env.NODE_ENV === 'production') return null
  return (
    <div
      role="note"
      className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-xs text-amber-900"
    >
      <strong>Dev mode test login:</strong>{' '}
      <code className="rounded bg-amber-100 px-1 py-0.5">admin@test.local</code>{' '}
      /{' '}
      <code className="rounded bg-amber-100 px-1 py-0.5">testpass123</code>
      {' '}— seeded by <code>pb_migrations/_seed_test_user.js</code> (or your backend equivalent). Never rendered in production.
    </div>
  )
}
```

Wire it into the root layout (`src/app/layout.tsx`) above `{children}`:

```tsx
import { DevCredentialsBanner } from '@/components/DevCredentialsBanner'
// ...
<body>
  <DevCredentialsBanner />
  {children}
</body>
```

README.md `## Local Development` section — copy verbatim:

```markdown
## Local Development

Test login (seeded automatically on first run):

- Email: `admin@test.local`
- Password: `testpass123`

Credentials also shown as a dev-mode banner at the top of every page; banner is stripped from production builds.
```

## Build & Verify

```bash
npm run build   # type-checks + builds
npm run start   # production server
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
npm install
exec npm run dev -- -H 0.0.0.0 -p 3000
```

## Pairing

- **+ PocketBase** → Next.js frontend, PocketBase backend (API proxy in next.config)
- **+ Supabase Local** → Next.js + @supabase/ssr for auth + Postgres
- **+ SQLite** → Next.js API routes with better-sqlite3
