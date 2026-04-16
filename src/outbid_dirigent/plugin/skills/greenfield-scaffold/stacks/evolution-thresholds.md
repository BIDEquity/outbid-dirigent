# Evolution Thresholds

**Purpose:** prototypes are not forever. Every scaffold choice has a point where it breaks. This doc lists those thresholds per stack, so the `<architecture-decisions>` section in ARCHITECTURE.md can record concrete migration triggers instead of vague "might need to replace later" handwaving.

**How to use:** when writing `### Evolution Thresholds` in ARCHITECTURE.md, look up your chosen stacks here, pick the thresholds that apply, and copy them in. Override with SPEC-specific numbers when the SPEC constrains scale explicitly.

## Thresholds Reference

### UI / Frontend

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **Streamlit** | ~10 concurrent users | Multi-tenancy needed / >10 concurrent / custom auth flows / SSR needed | Split UI into React (Vite+React or Next.js) + FastAPI backend |
| **Gradio** | Single-purpose demo | Multi-page app / routing / complex state | Switch to Streamlit, then to React |
| **Vite+React (SPA)** | Single user / read-heavy | SEO required / auth-gated content | Migrate to Next.js for SSR |
| **Next.js** | Mid-scale SaaS | Custom edge needs / multi-region / heavy server-side work | Add dedicated backend (FastAPI/NestJS); Next.js becomes pure UI |
| **Expo (Managed)** | Most mobile features | Custom native modules / App Store lock-down concerns | Expo prebuild / EAS / eject to bare workflow |

### Data / Storage

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **DuckDB (embedded)** | ~10GB data, read-heavy | Concurrent writers / network access / OLTP workload | Postgres via Supabase (keep DuckDB for analytics queries via `postgres_scanner` extension) |
| **SQLite** | ~1GB data, single writer | Network access / multi-writer / replication | Postgres via Supabase |
| **Supabase Local (Postgres)** | Per local machine | Team collaboration / cross-device access | Supabase Cloud (hosted) or self-hosted Postgres on VPS |
| **LanceDB** | <100GB vectors, single node | Clustered search / billion-scale vectors | Qdrant / Weaviate / pgvector (if data lives in Postgres already) |

### Backend / Compute

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **FastAPI (in-process)** | Single server | >1 instance / horizontal scaling | Add reverse proxy (Caddy/Nginx) + run multiple workers (gunicorn/uvicorn-workers) |
| **PocketBase** | ~100 active users / simple schemas | Complex RLS / OAuth providers / horizontal scale | Migrate to Supabase (schema export → PostgREST) |
| **Supabase Edge Functions** | Low-throughput webhooks | >100 req/s sustained / long-running work | Dedicated service (FastAPI on VPS) with queue |

### Events / Messaging

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **In-process pub/sub** (callbacks) | Single server instance | >1 server / events must survive restart | NATS / Redis Streams |
| **FastAPI BackgroundTasks** | Short, unimportant side effects | Must retry on failure / must survive restart / >1 server | Add a queue: Redis + RQ (simple) or Celery (complex) |
| **Supabase Realtime** | Per-user channels, <1000 concurrent | >1000 concurrent subscribers / custom routing | Dedicated WebSocket server (FastAPI + Redis pub/sub) |
| **Supabase Database Triggers** | Sync side effects <1s | Long-running triggers (>1s) / need retry | Move logic to Edge Functions or external worker via webhook |

### Auth / Identity

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **PocketBase auth** | Email/password only | OAuth providers needed / SSO / MFA / audit log | Add Clerk, Auth0, or Supabase Auth |
| **Supabase Auth (local)** | Full feature set, per-project | Enterprise SSO (SAML) / cross-product identity | Clerk, Auth0, WorkOS |
| **Custom JWT** | Never do this for a prototype | Always | Don't — use PocketBase or Supabase |

### LLM / Agent

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **Anthropic SDK (direct)** | Single-tenant, stateless calls | Multi-tenant rate limiting / cost tracking per user / tool auditing | Add a thin gateway (FastAPI) for rate limit, cost, audit |
| **In-memory conversation state** | Single user session | Multi-user / must persist across restart | Move state to DB (Postgres `conversations` table) |
| **In-process agent loop** | Loops <10 iterations, <30s | Long-running agents / parallel tool calls / user cancellation | Move to background worker with checkpointing |

### Deployment

| Component | Prototype limit | Migration trigger | Next step |
|---|---|---|---|
| **Local `start.sh`** | Dev machine / port-forward | Shared staging env / multiple engineers / HTTPS | Docker Compose on a VPS, then Kubernetes if scale demands |
| **No CI/CD** | Solo prototype | Team collaboration / audit trail / test gating | GitHub Actions (test on PR, deploy on merge to main) |
| **No monitoring** | Prototype | User-facing app / SLA requirements | Sentry for errors + basic uptime check (UptimeRobot) |

## Wallet / Hardware-Specific (ex: Cuseum VAM)

These need upfront planning — they can't be retrofit late:

| Component | Gotcha | Upfront action |
|---|---|---|
| **Apple Wallet Pass Type ID** | 1-2 weeks Apple Developer Program approval process | Register Pass Type ID on day 1, even if prototype uses dummy passes |
| **Apple Push Notification Service (APNs) cert** | Server cert must be generated during dev; changing it in production requires re-registration | Generate cert early; store in .env template |
| **Google Wallet API (issuer account)** | Requires Google Wallet Business Console setup | Register during prototype phase |
| **NFC on iOS** | Requires Core NFC entitlement from Apple — not available in Expo Go | Plan for EAS dev client or bare workflow from Day 1 if iOS NFC is in scope |

## How to Use in ARCHITECTURE.md

Copy the relevant rows into the `### Evolution Thresholds` block of `<architecture-decisions>`:

```markdown
### Evolution Thresholds

When to migrate away from this prototype:

| Component | Threshold | Next step |
|---|---|---|
| Streamlit UI | >10 concurrent users | Split to Next.js + FastAPI |
| DuckDB | >10GB | Postgres via Supabase |
| In-process events | >1 server | NATS / Redis Streams |

Upfront commitments (cannot be added late):
- Apple Wallet Pass Type ID — register now, 1-2 weeks approval
- APNs push cert — generate during dev
```

Keep it to 5-10 rows. Only list what applies to THIS project.

## Rules for Writing Thresholds

1. **Concrete numbers, not adjectives.** "10 GB" not "lots of data". "100 users" not "many users".
2. **Name the next step.** "Migrate to Postgres" not "might need a better database".
3. **Upfront commitments get their own subsection.** Hardware / developer-program / cert registrations that have lead time MUST be listed separately as "upfront" — they can't be deferred.
4. **If a threshold doesn't apply to this project, omit it.** A solo-user internal tool doesn't need concurrent-user thresholds.
5. **This block is for the reviewer and the human maintainer.** It's not executed; it's a commitment to future decisions.
