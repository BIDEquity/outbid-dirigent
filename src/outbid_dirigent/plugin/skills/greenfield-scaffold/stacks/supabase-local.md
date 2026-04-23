# Supabase Local

**Role:** Backend + Auth (production-grade) — Postgres, Auth, Storage, Edge Functions, Studio UI
**Tier:** 1 (default for production backend with auth)
**When:** SPEC needs real Postgres, complex auth (OAuth, RLS), file storage, or the Studio dashboard for non-techie data management

**Requires:** Docker running on the workspace

## Docs

Before using unfamiliar Supabase APIs, query context7:
1. `mcp__context7__resolve-library-id` with `libraryName="supabase"` → get libraryId
2. `mcp__context7__query-docs` with `libraryId=<result>` and `topic="<your question>"` → get current docs

## Check Installation

```bash
supabase --version
docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker NOT running"
```

If either command fails, **do not stop** — follow the Fallback chain below.

## Fallback chain

When `supabase start` cannot run (no Docker daemon, no `supabase` CLI, image pulls blocked, port conflicts that can't be freed), fall back through these tiers in order. Record the active tier in `ARCHITECTURE.md` → `### Backend Fallback Level` per Step 2 of SKILL.md. Do not silently continue with the primary as if it worked — the e2e suite won't run and reviews will mask it as `warn — infra not running`.

### Tier 1: primary (Supabase Local)

```bash
supabase start
```

If that prints connection URLs: use the stack as documented. Done.

### Tier 2: Postgres on Docker (lose Supabase Auth, keep Postgres)

When Docker works but Supabase's bundled services (Auth, Storage, Studio, Edge Functions) can't start — commonly image-pull failures, disk-space limits, or workspace port restrictions.

Start a plain Postgres container:

```bash
docker run -d --name app-pg \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=app \
  -p 54322:5432 \
  postgres:16
```

Wait for readiness with a pg_isready loop (see the NextJS stack file for a portable `until pg_isready` snippet).

Apply migrations with `psql` piped into the container — one file at a time — then feed `supabase/seed.sql` in the same way. The exact shell pipeline lives next to the per-stack docs; keep this skill file declarative.

**What you lose vs Tier 1** (must be captured in `ARCHITECTURE.md` → Future Considerations):

- **Supabase Auth gone.** Roll a minimal email/password auth: hash passwords with `bcryptjs` at the Server Action layer, store sessions in a `sessions` table, set an HTTP-only cookie. Test user (`admin@test.local` / `testpass123`) gets inserted by the seed script with a pre-hashed password.
- **No realtime, no storage, no Edge Functions.** If the SPEC relies on these, flag as `DEVIATION: tier-2-fallback — realtime feature deferred until Docker/Supabase are available`.
- **RLS still works** (it's a Postgres feature), but `auth.uid()` does not exist — replace with your session-table lookup function.

`NEXT_PUBLIC_SUPABASE_URL` stays pointed at a local API you write yourself (Next.js Route Handlers hitting Postgres directly). Or simpler: skip `@supabase/ssr` entirely and use the `postgres` npm package from Server Components.

### Tier 3: SQLite in-process (no external dependencies)

When Docker itself is not available on the workspace — common in strict sandboxes, CI ephemeral runners with no Docker-in-Docker, or locked-down corporate environments.

For Next.js:

```bash
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

Create a thin DB module (`src/lib/db.ts`) that instantiates `better-sqlite3`, enables WAL journal mode, enforces foreign keys, and exports a single `db` handle. Keep it small — ~10 lines.

Translate the Supabase migrations to SQLite dialect at scaffold time:

- `UUID` → `TEXT` (generate with `crypto.randomUUID()` in the app layer)
- `TIMESTAMPTZ DEFAULT now()` → `TEXT DEFAULT (datetime('now'))`
- `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` → drop (enforce access control in Server Actions)
- `gen_random_uuid()` → application-side `crypto.randomUUID()`
- `jsonb` → `TEXT` + `JSON.stringify` / `JSON.parse` helpers
- `pg_cron` → `node-cron` or a simple `setInterval` in a long-running process

Apply migrations at boot using an idempotent loop: create a `_migrations` tracking table on first run, then replay each `.sql` file that isn't already recorded there. Keep the loop in `src/lib/migrate.ts`; call it once from app startup. No ORMs, no migration frameworks.

**What you lose vs Tier 2** (must be captured in `ARCHITECTURE.md`):

- **Single-writer only.** SQLite serialises writes; fine for prototype, not for production.
- **No network database access** — everything runs in the Next.js process. Good for dev, but you can't point a second service at the same DB without contention.
- **No Postgres extensions** — if the SPEC calls out `pg_trgm`, `pgvector`, `postgis`, flag as `DEVIATION: tier-3-fallback — <extension> requires Postgres, feature deferred`.
- **No Postgres-specific SQL** — watch for `UPSERT` syntax differences, `jsonb_path_query`, window functions with unsupported framing.

### Tier 4 (analytical only): DuckDB in-process

Only use DuckDB if the SPEC is overwhelmingly read-heavy (dashboards over columnar data) and has no concurrent-write requirement. For transactional / auth-bearing apps, go SQLite at Tier 3 instead. DuckDB is documented here for completeness, not as a general fallback.

### Record the active tier

After the fallback resolves, write this block into `ARCHITECTURE.md` `<architecture-decisions>`:

```markdown
### Backend Fallback Level

- Primary (Supabase Local) attempted: FAILED — {reason}
- Tier 2 (Postgres on Docker) attempted: {OK|FAILED — reason|SKIPPED}
- Tier 3 (SQLite in-process) attempted: {OK|SKIPPED}
- **Active backend:** {Supabase Local | Postgres on Docker | SQLite in-process}
- **Lost capabilities vs primary:** {e.g. "Supabase Auth replaced by hand-rolled session cookies; no realtime; no storage"}
- **Upgrade path:** When Docker becomes available, migrate to Supabase Local by running `supabase init && supabase db reset` and re-wiring `NEXT_PUBLIC_SUPABASE_URL`. Migrations are compatible; only the auth layer needs to swap back to `@supabase/ssr`.
```

Update `test-harness.json` `notes` with the active tier so the contract negotiator writes realistic verification commands.

## Scaffold

```bash
supabase init
supabase start
```

`supabase start` pulls Docker images and starts all services. First run takes a few minutes.

After start, it prints connection details:

```
API URL:        http://localhost:54321
GraphQL URL:    http://localhost:54321/graphql/v1
Studio URL:     http://localhost:54323
Anon key:       eyJ...
Service role:   eyJ...
DB URL:         postgresql://postgres:postgres@localhost:54322/postgres
```

Create schema via migrations:

```bash
supabase migration new create_items
```

```sql
-- supabase/migrations/20240101000000_create_items.sql
CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
  created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE items ENABLE ROW LEVEL SECURITY;

CREATE POLICY "items are viewable by everyone"
  ON items FOR SELECT USING (true);
```

```bash
supabase db reset   # apply migrations
```

## Run

```bash
supabase start
```

Ports:
- **54321** — API (REST + GraphQL)
- **54322** — Postgres direct
- **54323** — Studio (admin UI for non-techies)

## Test

```bash
# Health check
curl -s http://localhost:54321/rest/v1/ \
  -H "apikey: <anon-key>" | head -1

# Insert record
curl -s -X POST http://localhost:54321/rest/v1/items \
  -H "apikey: <anon-key>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Item"}'

# Query records
curl -s http://localhost:54321/rest/v1/items \
  -H "apikey: <anon-key>"
```

For Python integration tests:

```bash
uv add supabase
uv add --dev pytest
```

```python
# tests/test_supabase.py
from supabase import create_client

SUPABASE_URL = "http://localhost:54321"
SUPABASE_KEY = "<anon-key-from-supabase-start>"

def test_connection():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("items").select("*").execute()
    assert result.data is not None

def test_insert_and_read():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.table("items").insert({"title": "Test"}).execute()
    result = client.table("items").select("*").eq("title", "Test").execute()
    assert len(result.data) >= 1
```

```bash
uv run pytest tests/ -v
```

## Stop

```bash
supabase stop        # stop containers
supabase stop --no-backup  # stop and discard data
```

## Start Script Pattern

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"
supabase start
echo "Studio UI: http://localhost:54323"
echo "API: http://localhost:54321"
# Start the frontend (if any)
# npm run dev -- --host 0.0.0.0 --port 3000
```

## Pairing

- **+ Next.js** → @supabase/ssr for auth + Postgres via Supabase client
- **+ Vite+React** → @supabase/supabase-js for direct Postgres access
- **+ FastAPI** → Connect to Postgres at localhost:54322 via psycopg2/asyncpg
- **+ Streamlit** → supabase-py client for data access
