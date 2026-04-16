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
