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
