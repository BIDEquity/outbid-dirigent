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
