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

## Stock Landing Replacement

Immediately after `create-next-app`, overwrite `src/app/page.tsx`. The stock file is a Vercel tutorial with logos, "Get started by editing…", and Deploy-Now buttons — it MUST go before the first real phase starts, otherwise every e2e smoke passes against framework-starter content.

Minimal template (adjust the `<h1>` text to the SPEC's working title, `/login` to the first real route):

```tsx
// src/app/page.tsx
import Link from 'next/link'

export default function Home() {
  return (
    <main className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-xl flex-col items-center justify-center gap-6 px-6 text-center">
      <h1 className="text-3xl font-semibold tracking-tight">{APP_TITLE}</h1>
      <p className="text-sm text-zinc-600">
        {ONE_LINE_DESCRIPTION_FROM_SPEC}
      </p>
      <Link
        href="/login"
        className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
      >
        Sign in
      </Link>
    </main>
  )
}
```

Also delete the scaffold's `src/app/page.module.css` if it exists — the template above uses Tailwind utility classes only.

Auth-less apps: swap the `/login` link for the first nav target the SPEC mentions (e.g. `/dashboard`, `/search`). The point is that clicking leads somewhere real, not to a 404.

## Authenticated Entry (NavShell + Dashboard)

For SPECs that name authenticated user roles, scaffold the navigable shell at `/dashboard` before any feature phase starts. The shell is intentionally minimal — one role-gated link per primary feature surface. Downstream phases flesh out the linked pages; the shell keeps the navigation surface present from day one so e2e specs have something real to assert against.

`src/components/NavShell.tsx` — reads the current user's role and renders the matching link set. Replace `ROLES` and `LINKS` with what the SPEC actually names.

```tsx
// src/components/NavShell.tsx
import Link from 'next/link'
import type { ReactNode } from 'react'

// Derive these from the SPEC's role model — do not invent roles.
type Role = 'admin' | 'project_manager' | 'resource_manager' | 'employee'

// One entry per primary feature surface named in the SPEC.
// `roles` is the allowlist; routes may 404 until their feature lands —
// that is fine, the shell exists so feature phases have a target.
const LINKS: ReadonlyArray<{ href: string; label: string; roles: readonly Role[] }> = [
  { href: '/skills',             label: 'Manage Skills',     roles: ['admin', 'resource_manager'] },
  { href: '/team',               label: 'My Team',           roles: ['resource_manager'] },
  { href: '/projects',           label: 'Projects',          roles: ['project_manager'] },
  { href: '/requests',           label: 'Resource Requests', roles: ['project_manager', 'resource_manager'] },
  { href: '/time',               label: 'My Time',           roles: ['employee'] },
  { href: '/admin/sync-log',     label: 'HRIS Sync Log',     roles: ['admin'] },
]

export function NavShell({ role, children }: { role: Role; children: ReactNode }) {
  const visible = LINKS.filter((l) => l.roles.includes(role))
  return (
    <div className="flex min-h-screen">
      <nav
        aria-label="Main navigation"
        className="flex w-56 shrink-0 flex-col border-r border-zinc-200 bg-white px-3 py-6"
      >
        <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Navigation
        </p>
        <ul className="flex flex-col gap-0.5">
          {visible.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="block rounded-md px-3 py-2 text-sm text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900"
                data-testid={`nav-${l.href.slice(1).replace(/\//g, '-')}`}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  )
}
```

`src/app/dashboard/page.tsx` — the authenticated landing that uses the shell. Adjust the auth lookup to match the chosen backend (Supabase SSR / PocketBase / custom).

```tsx
// src/app/dashboard/page.tsx
import { redirect } from 'next/navigation'
import { NavShell } from '@/components/NavShell'
// import { getCurrentUser } from '@/lib/auth'  // ← stack-specific; fill in

export default async function DashboardPage() {
  // Stack-specific: resolve the authenticated user and role.
  // Example shape:
  //   const user = await getCurrentUser()
  //   if (!user) redirect('/login')
  const user = { email: 'admin@test.local', role: 'admin' as const }  // replace with real lookup
  if (!user) redirect('/login')

  return (
    <NavShell role={user.role}>
      <section className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Signed in as <strong>{user.email}</strong>
        </p>
        <p className="mt-6 text-sm text-zinc-500">
          Use the navigation on the left to access the app.
        </p>
      </section>
    </NavShell>
  )
}
```

**Do not feature-build the dashboard here.** Widgets, charts, activity feeds — all of that belongs in feature phases. The scaffold only produces:

- The `/dashboard` route that auth redirects to
- The `NavShell` with role-gated links to every surface the SPEC names
- A placeholder body that proves auth + routing work

Every nav link should point to a route the planner will populate in a later phase. If a SPEC-named feature has no link in `LINKS`, the planner has no target — add it. If a link points to a route no phase will populate, remove it from the SPEC or the shell before committing.

**Verify before moving on:** `curl -sf http://localhost:3000/dashboard` returns HTML containing at least one `data-testid="nav-..."` element per role the SPEC names.

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

test('home page renders without console errors', async ({ page }) => {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []

  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (err) => {
    pageErrors.push(`${err.name}: ${err.message}`)
  })

  await page.goto('/')
  await expect(page.locator('body')).toBeVisible()

  // Hydration mismatches, missing imports, and runtime React errors
  // all surface here — not catching them means "body visible" passes
  // against an app that is visibly broken in the console.
  expect(
    { consoleErrors, pageErrors },
    `home page should not emit console or runtime errors`
  ).toEqual({ consoleErrors: [], pageErrors: [] })
})
```

Why both listeners: `console` catches explicit `console.error(...)` calls and React's dev-mode hydration warnings; `pageerror` catches uncaught exceptions that don't go through `console`. A hydration mismatch (the failure mode in little-erp) produces a `console` error; an undefined-variable ReferenceError produces a `pageerror`.

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

PORT="${PORT:-3000}"

npm install

cat <<BANNER
──────────────────────────────────────────
  App URL        : http://localhost:${PORT}
  Test login     : admin@test.local / testpass123
                   (seeded on first run; dev-mode banner on every page)
  Override port  : PORT=4000 ./start.sh
──────────────────────────────────────────
BANNER

exec npm run dev -- -H 0.0.0.0 -p "$PORT"
```

## Pairing

- **+ PocketBase** → Next.js frontend, PocketBase backend (API proxy in next.config)
- **+ Supabase Local** → Next.js + @supabase/ssr for auth + Postgres
- **+ SQLite** → Next.js API routes with better-sqlite3
