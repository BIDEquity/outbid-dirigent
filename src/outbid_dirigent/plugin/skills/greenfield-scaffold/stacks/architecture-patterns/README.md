# Architecture Patterns — Three Axes

Architecture is not one dimension. For greenfield projects, pick **three things**:

1. **Interaction Shape** — how clients talk to the system (5 options)
2. **Compute Topology** — where the code runs (3 options)
3. **Domain Pattern** (optional) — the shape of the problem itself (Pipeline, Agent Loop, State Machine, …)

Most prototypes pick one from each axis. **Default: Sync REST × In-Process × (no domain pattern)** — covers ~80% of prototypes.

The "7 patterns" this file used to list were a grab-bag that mixed all three axes. The sections below split them properly. Existing pattern files (sync-rest.md, streaming.md, etc.) are the detailed references — this README is the index.

---

## Axis 1: Interaction Shape (5 options)

How the client interacts with the server. Pick exactly one primary shape per service. A prototype may combine two (e.g. Sync REST + Batch), rarely three.

| Shape | Core Idea | Domain Signal | Detail |
|---|---|---|---|
| **Sync REST / CRUD** | Request → Response | "user views list, edits items", "admin panel" | [sync-rest.md](sync-rest.md) |
| **Streaming** | Continuous output during production | "live updates", "as it happens", "progress" | [streaming.md](streaming.md) |
| **Event-Driven** | Publisher fires → Subscribers react independently | "when X happens, then Y, Z, W" | [event-driven.md](event-driven.md) |
| **Real-time / Collaborative** | Shared state, multiple clients | "live collaborative", "shared editing" | [real-time.md](real-time.md) |
| **Batch / Scheduled** | Periodic processing, no user wait | "nightly", "hourly", "cron" | [batch.md](batch.md) |

**Default:** Sync REST / CRUD.

---

## Axis 2: Compute Topology (3 options)

Where the code executes. This determines deployment, scaling, and operational profile.

| Topology | What it means | When to pick | Stacks that fit |
|---|---|---|---|
| **In-Process** | Single long-lived process handles all requests | Default for prototypes. Simple to reason about, simple to run (`./start.sh`). Scales vertically only. | FastAPI (uvicorn), Streamlit, Gradio, Next.js dev, Expo Metro |
| **Serverless / Edge** | Each request spawns (or hits warm) a short-lived function | When you have bursty traffic, need per-request isolation, or use Supabase/Vercel Edge Functions | Supabase Edge Functions, Next.js Route Handlers on Vercel, Cloudflare Workers |
| **Long-running Worker** | Dedicated process(es) consuming work off a queue or schedule | When work is async / needs retries / takes minutes / must survive HTTP timeouts | FastAPI + APScheduler, dedicated Python worker, Supabase pg_cron |

**Default:** In-Process. Switch to Serverless only if the stack is natively serverless (Supabase Edge, Vercel). Switch to Worker when you have batch or long-running agent work.

**Evolution:** most prototypes start In-Process and add a Worker sidecar when the first task exceeds a few seconds. Going to Serverless is usually a deployment-stage decision, not a prototype decision.

---

## Axis 3: Domain Patterns (optional)

These describe the **shape of the problem**, not the shape of the architecture. They're application patterns, not architecture patterns — but they heavily influence how you structure the code inside your chosen Interaction Shape × Compute Topology.

Only add a domain pattern when the SPEC's problem matches. Most prototypes need zero.

| Pattern | When the SPEC matches | Combines with | Detail |
|---|---|---|---|
| **Pipeline / ETL** | "ingest → validate → transform → export", N sequential stages with clear I/O | Batch or Sync REST | [pipeline.md](pipeline.md) |
| **Agent Loop** | LLM with tool use, self-directed problem solving | Streaming (for intermediate thoughts), Sync REST (wrapper API) | [agent-loop.md](agent-loop.md) |
| **State Machine / Workflow** | Entity has sequential states with rules (e.g. visit: scanned → validated → logged → notified), error paths matter | Event-Driven or Sync REST | — (not yet documented; see anti-patterns below) |
| **Webhook Receiver** | "when Stripe fires", "when GitHub pushes" — external trigger | Usually implies Serverless topology | — (use Event-Driven + FastAPI webhook endpoints) |
| **Multi-Tenant Isolation** | One app, many customers, data must not leak across tenants | Orthogonal — applies regardless of other axes | — (use Supabase RLS or tenant_id column + enforcement) |

**Anti-pattern warning:** do NOT treat "Event-Driven" as a substitute for "State Machine". A visit lifecycle (`scan → validate → log → notify`) with error paths (`expired pass → reject`) is a State Machine. Raw Event-Driven fan-out loses ordering and error recovery. If the SPEC has sequential state with rules, write it as an explicit state machine — one function per transition, one table column for `state`, and let domain.py own the transitions.

---

## Pattern × Stack Compatibility Matrix

**Check this before committing.** Your stack must be ✓ (or at worst △) for your chosen Interaction Shape. If ✗, switch stack or shape.

**Legend:** ✓ fits well | △ possible but not ideal | ✗ wrong tool

| Stack \ Interaction Shape | [Sync REST](sync-rest.md) | [Streaming](streaming.md) | [Event-Driven](event-driven.md) | [Real-time](real-time.md) | [Batch](batch.md) |
|---|---|---|---|---|---|
| **Streamlit** | ✓ | ✓ (`st.write_stream`) | ✓ (in-process pub/sub works; cross-session does not) | △ (session only, no cross-user sync) | ✗ |
| **Gradio** | ✓ | ✓ (yield) | △ (single-session only) | ✗ | ✗ |
| **Vite+React** | ✓ (fetch/SWR) | ✓ (SSE, EventSource) | ✓ | ✓ (WebSocket) | ✗ |
| **Next.js** | ✓ (Server Components + Actions) | ✓ (Streaming RSC) | ✓ (Actions, webhooks) | ✓ (WS/SSE) | △ (via external cron) |
| **Expo (React Native)** | ✓ | ✓ | ✓ (notifications, hooks) | ✓ (WebSocket) | ✗ |
| **Astro (static mode)** | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Astro (SSR mode / API Routes)** | ✓ | △ | △ | △ | ✗ |
| **Astro Starlight** | ✗ (docs only) | ✗ | ✗ | ✗ | ✗ |
| **FastAPI** | ✓ (canonical) | ✓ (StreamingResponse) | ✓ (webhooks, BG tasks) | ✓ (WebSocket) | ✓ (APScheduler) |
| **PocketBase** | ✓ (built-in REST) | ✓ (Realtime subs) | ✓ (pb_hooks in JS, Realtime) | ✓ (made for it) | ✗ (no scheduler) |
| **Supabase Local** | ✓ (PostgREST) | ✓ (Realtime) | ✓ (Triggers, Edge Fns) | ✓ (made for it) | ✓ (pg_cron) |
| **Anthropic SDK** | ✓ | ✓ (`messages.stream`) | ✓ (tool_use callbacks) | △ | ✓ |
| **Clerk** | auth-orthogonal — pairs with any frontend stack; does not constrain Interaction Shape | | | | |
| **SQLite / DuckDB / LanceDB** | pattern-neutral — embedded storage used by any stack | | | | |

**Key Takeaways:**
- **FastAPI** and **Supabase Local** are the most versatile backends (support all shapes)
- **Streamlit/Gradio** are strong for Sync/Streaming, weak for Real-time (session isolation)
- **Astro**: Starlight is static; plain Astro in SSR mode supports dynamic patterns
- **PocketBase** now listed as ✓ for Event-Driven (has `pb_hooks` in JavaScript — earlier "no custom code" was wrong). Weak only for Batch (no scheduler).

---

## Compute Topology × Stack Compatibility

Which stacks naturally fit which topology:

| Stack | In-Process | Serverless | Long-running Worker |
|---|---|---|---|
| Streamlit / Gradio | ✓ native | ✗ | ✗ |
| FastAPI | ✓ native | △ (Vercel Python) | ✓ (+ APScheduler / RQ) |
| Next.js | ✓ (dev) / △ (prod) | ✓ (Vercel native) | ✗ |
| Supabase Edge Functions | ✗ | ✓ native | ✗ |
| PocketBase | ✓ native | ✗ | ✗ |
| Dedicated Python script | ✓ | ✗ | ✓ native |

---

## Decision Signals — SPEC → Interaction Shape

| If the SPEC says... | Shape |
|---|---|
| "user views list, edits items", "CRUD", "admin panel" | Sync REST (default) |
| "live", "streaming", "as it happens", "progress updates" | Streaming |
| "when X happens then Y", "notify", "trigger", "webhook", "on scan" | Event-Driven |
| "collaborative", "multi-user live", "shared editing", "kanban" | Real-time |
| "nightly", "hourly", "cron", "scheduled", "batch" | Batch |

When in doubt → Sync REST + In-Process.

---

## Language in Code Examples

Each pattern file includes a Python code skeleton for concreteness. **Python is shown as an example — the pattern applies equally to TypeScript, JavaScript, Go, etc.** Check your stack's entry in the matrix above and its individual stack file for language-specific library names.

---

## Shape Interaction (when to combine)

Most prototypes use **one primary Interaction Shape**. Occasionally two shapes combine:

- **Sync REST + Streaming**: REST endpoints, but `/api/chat` streams while `/api/history` is sync
- **Sync REST + Batch**: CRUD app with a nightly job
- **Event-Driven + Sync REST**: REST endpoints fire events that trigger side effects
- **Streaming + Agent Loop (domain pattern)**: agent iterates, but streams its intermediate thoughts

Avoid three+ primary shapes in one prototype. That's when you outgrow the archetype and need a proper architecture design (not a greenfield scaffold).
