# PocketBase

**Role:** Backend + Auth (lightweight) — instant REST API, auth, SQLite, admin UI
**Tier:** 1 (default for lightweight backend with auth)
**When:** SPEC needs auth + database + API with minimal code. No Docker required.

## Docs

Before using unfamiliar PocketBase APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="pocketbase"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
pocketbase --help
# or check binary exists:
which pocketbase || ls ./pocketbase
```

## Scaffold

No scaffold needed. PocketBase is a single binary. On first run it creates `pb_data/` and `pb_migrations/`.

Define collections via migration files:

```javascript
// pb_migrations/001_initial.js
migrate((app) => {
  const collection = new Collection({
    name: "items",
    type: "base",
    schema: [
      { name: "title", type: "text", required: true },
      { name: "description", type: "text" },
      { name: "status", type: "select", options: { values: ["draft", "published"] } },
    ],
  })
  app.save(collection)
})
```

## Run

```bash
pocketbase serve --http 0.0.0.0:8090
```

Port: **8090** (API + Admin UI)
Admin UI: `http://localhost:8090/_/`

On first run, create admin account at the Admin UI URL.

## Test

Test via HTTP requests against the running instance:

```bash
# Health check
curl -s http://localhost:8090/api/health | grep -q '"code":200'

# Create record
curl -s -X POST http://localhost:8090/api/collections/items/records \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Item"}' | grep -q '"id"'

# List records
curl -s http://localhost:8090/api/collections/items/records | grep -q '"items"'
```

For Python integration tests:

```bash
uv add --dev pytest httpx
```

```python
# tests/test_pocketbase.py
import httpx

BASE = "http://localhost:8090"

def test_health():
    r = httpx.get(f"{BASE}/api/health")
    assert r.status_code == 200

def test_create_and_list():
    r = httpx.post(f"{BASE}/api/collections/items/records",
                   json={"title": "Test"})
    assert r.status_code == 200
    record_id = r.json()["id"]

    r = httpx.get(f"{BASE}/api/collections/items/records/{record_id}")
    assert r.json()["title"] == "Test"
```

```bash
uv run pytest tests/ -v
```

## Test User Seed (mandatory for web archetypes with auth)

Idempotent migration that creates `admin@test.local / testpass123` on first run:

```javascript
// pb_migrations/1700000000_seed_test_user.js
migrate((app) => {
  const users = app.findCollectionByNameOrId("users")
  try {
    app.findAuthRecordByEmail("users", "admin@test.local")
    return  // already seeded
  } catch (_) {
    // fall through and create
  }
  const record = new Record(users, {
    email: "admin@test.local",
    emailVisibility: true,
    verified: true,
    name: "Test Admin",
  })
  record.setPassword("testpass123")
  app.save(record)
})
```

The `try/catch` on `findAuthRecordByEmail` keeps the migration idempotent — re-running `pocketbase serve` never errors and never creates duplicates. Document the resulting credentials in README.md and the dev-mode banner (see `stacks/nextjs.md` → "Dev Credentials Banner").

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

PORT="${POCKETBASE_PORT:-8090}"

cat <<BANNER
──────────────────────────────────────────
  PocketBase API : http://localhost:${PORT}
  Admin UI       : http://localhost:${PORT}/_/
  Test login     : admin@test.local / testpass123
                   (seeded by pb_migrations/*_seed_test_user.js)
  Override port  : POCKETBASE_PORT=9000 ./start.sh
──────────────────────────────────────────
BANNER

exec pocketbase serve --http "0.0.0.0:${PORT}"
```

## Pairing

- **+ Vite+React** → PocketBase backend, React SPA frontend (pocketbase-js SDK)
- **+ Next.js** → PocketBase backend, Next.js fullstack frontend
- **+ Streamlit** → PocketBase for auth/users, Streamlit for data UI
- **+ FastAPI** → PocketBase for auth, FastAPI for custom business logic
