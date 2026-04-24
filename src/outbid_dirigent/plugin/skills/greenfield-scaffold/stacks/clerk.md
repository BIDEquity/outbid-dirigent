# Clerk

**Role:** Auth (managed SaaS) — sign-up, sign-in, sessions, organizations, social logins, MFA
**Tier:** 1 (default for managed auth when SPEC explicitly demands OAuth/SSO/social-login/managed-identity)
**When:** SPEC names OAuth providers, SSO, social login, managed user dashboard, organizations/teams, or compliance/audit needs that PocketBase / Supabase Auth don't cover. **Do not** pick Clerk just because the SPEC says "users can log in" — that's covered by PocketBase or Supabase Local with zero external dependencies.

**Requires:** internet access. Clerk's Frontend API is hosted — no air-gapped operation.

## Docs

Before using unfamiliar Clerk APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="Clerk"` → get libraryId (`/clerk/clerk-docs`)
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

Clerk has no CLI binary to install — verify only that the npm package resolves:

```bash
npm view @clerk/nextjs version > /dev/null && echo "Clerk SDK reachable"
```

(Adjust package name to the chosen frontend SDK: `@clerk/nextjs`, `@clerk/react-router`, `@clerk/astro`, `@clerk/tanstack-react-start`.)

## Scaffold

Pick the SDK that matches the frontend stack:

```bash
# Next.js (App Router)
npm install @clerk/nextjs

# Vite + React Router (KEYLESS-CAPABLE — see Pairing notes)
npm install @clerk/react-router react-router

# Astro
npm install @clerk/astro

# TanStack Start
npm install @clerk/tanstack-react-start
```

Then wrap the app root with the framework's `<ClerkProvider>` per the SDK's quickstart. **Do not** set `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` or `CLERK_SECRET_KEY` in `.env` — leaving them unset activates **Keyless Mode** (see below).

## Keyless Mode (default for prototypes)

When `*_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` are absent, Clerk auto-generates temporary keys at first run. The app boots, sign-up/sign-in works, no Clerk account needed.

A "Configure your application" prompt appears in the running UI — the user clicks it later to associate the temporary keys with a real Clerk account ("claim"). The prototype never blocks on this step.

**Supported frameworks (Core 3, March 2026):** Next.js, TanStack Start, Astro, React Router (`@clerk/react-router`).

**NOT supported in Keyless Mode:** bare `@clerk/clerk-react` in Vite without React Router, `@clerk/expo`. These need a real Clerk account + env vars before scaffold.

Source: [Clerk Core 3 Changelog](https://clerk.com/changelog/2026-03-03-core-3).

## Run

Clerk runs *inside* the frontend stack — no separate process, no port. Start the frontend per its own stack file (e.g. `npm run dev` for Next.js on port 3000), and Clerk attaches via `<ClerkProvider>`.

## Test

### Unit / component tests

Mock `@clerk/<sdk>` hooks (`useAuth`, `useUser`, `useSignIn`) per the SDK's testing docs. No special infrastructure.

### E2E (Playwright) — uses Clerk Test Mode

Clerk has a built-in **Test Mode** for development instances (Keyless qualifies). Two primitives:

1. **Test email pattern:** any email containing `+clerk_test` (e.g. `admin+clerk_test@example.com`) is treated as a test address. Clerk does NOT send a real email; the verification code is always `424242`.
2. **Test phone pattern:** numbers in the `+1555*` range (e.g. `+15555550100`) accept the same `424242` code.

Install Clerk's Playwright helper:

```bash
npm install -D @clerk/testing
```

Use `setupClerkTestingToken` to bypass bot protection in test runs:

```typescript
// tests/e2e/auth.spec.ts
import { setupClerkTestingToken } from '@clerk/testing/playwright'
import { test, expect } from '@playwright/test'

test('sign up with test email', async ({ page }) => {
  await setupClerkTestingToken({ page })
  await page.goto('/sign-up')

  const email = `admin+clerk_test_${Date.now()}@example.com`
  await page.locator('input[name=emailAddress]').fill(email)
  await page.locator('input[name=password]').fill('TestPass123!')
  await page.getByRole('button', { name: 'Continue', exact: true }).click()

  await page.waitForResponse((r) => r.url().includes('prepare_verification') && r.status() === 200)
  await page.getByRole('textbox', { name: 'Enter verification code' }).pressSequentially('424242')

  await expect(page).toHaveURL(/\/dashboard|\//)
})
```

Source: [Clerk Test Mode docs](https://clerk.com/docs/guides/development/testing/test-emails-and-phones), [Playwright integration](https://clerk.com/docs/guides/development/testing/playwright/test-sign-up-flows).

## Test User Seed (Clerk-specific deviation)

The portfolio convention is to seed `admin@test.local / testpass123` at scaffold time so a developer can `git clone && ./start.sh` and immediately log in. **Clerk-based scaffolds cannot honour that convention** — Keyless Mode regenerates keys on every restart, so there is no stable `CLERK_SECRET_KEY` for a seed script to call the Backend API with.

Document the deviation in `README.md` under `## Local Development`:

```markdown
## Local Development

This app uses Clerk for authentication in Keyless Mode (no Clerk account required).

To log in:

1. Open the app at http://localhost:3000
2. Click **Sign Up** and use a test email like `admin+clerk_test@example.com`
3. Enter the verification code `424242` when prompted
4. You're in.

The `+clerk_test` subaddress and `424242` code are Clerk Test Mode features active in
development instances — no real emails are sent. See https://clerk.com/docs/guides/development/testing/test-emails-and-phones.

To upgrade to a permanent Clerk instance, click "Configure your application" in the
running app and follow the prompt to claim your keys.
```

Mount a dev-mode banner that shows the test email format (analogous to the standard banner in `stacks/vite-react.md` → "Dev Credentials Banner"):

```tsx
// src/components/ClerkDevBanner.tsx
export function ClerkDevBanner() {
  if (process.env.NODE_ENV !== 'development') return null
  return (
    <div role="note" style={{ background: '#fffbeb', borderBottom: '1px solid #fcd34d', padding: '8px 16px', fontSize: 12, color: '#78350f' }}>
      <strong>Dev mode (Clerk Keyless):</strong> sign up with{' '}
      <code>your+clerk_test@example.com</code> · verification code <code>424242</code>
    </div>
  )
}
```

## Start Script Pattern

Clerk has no own process. The stack-partner's `start.sh` is unchanged — Keyless Mode means no env-var setup is needed, so the existing Next.js / Vite / Astro start script already works.

Add a banner line documenting the Clerk-specific login flow:

```bash
cat <<BANNER
──────────────────────────────────────────
  App URL        : http://localhost:${PORT}
  Auth (Clerk)   : Keyless Mode — no account needed
  Test sign-up   : your+clerk_test@example.com / code 424242
  Claim keys     : click "Configure your application" in the running app
──────────────────────────────────────────
BANNER
```

## Pairing

- **+ Next.js** → `@clerk/nextjs` — Tier 1, Keyless Mode supported. Default for "Full-stack app with social login".
- **+ Vite+React + React Router** → `@clerk/react-router` — Tier 1, Keyless Mode supported. **Vite alone is not enough** — see `stacks/vite-react.md` "When paired with Clerk" block; React Router is mandatory.
- **+ Astro** → `@clerk/astro` — Tier 1, Keyless Mode supported. Use only if the SPEC needs auth on otherwise-static content (most Astro-Starlight docs sites do not).
- **+ TanStack Start** → `@clerk/tanstack-react-start` — Tier 1, Keyless Mode supported.
- **+ Expo** → `@clerk/expo` — Tier 2 (no Keyless). Requires a real Clerk account and `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` in `.env` before scaffold.
- **+ FastAPI / any backend** → Clerk handles identity at the frontend; the backend verifies sessions with Clerk's JWT verification (`@clerk/backend` for Node, JWKS lookup for Python). The backend stack stays whatever it is — Clerk is orthogonal.
