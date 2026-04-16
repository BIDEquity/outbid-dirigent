# Architecture Patterns — By The Book

Pick an architecture pattern based on the domain problem, not on the stack.
**Default: Sync REST / CRUD** (covers ~80% of prototypes).

Only pick a non-default pattern when the SPEC explicitly demands it. The seven
patterns below are what Claude knows well from its training corpus — staying
within them produces cleaner code than inventing custom shapes.

## Pattern × Stack Compatibility Matrix

**Check this first.** Before committing to a combo, verify your stack supports
your chosen pattern. If the cell isn't ✓, either switch stack or switch pattern.

**Legend:** ✓ fits well | △ possible but not ideal | ✗ wrong tool

| Stack \ Pattern | [Sync REST](sync-rest.md) | [Streaming](streaming.md) | [Event-Driven](event-driven.md) | [Pipeline / ETL](pipeline.md) | [Agent Loop](agent-loop.md) | [Real-time](real-time.md) | [Batch](batch.md) |
|---|---|---|---|---|---|---|---|
| **Streamlit** | ✓ | ✓ (`st.write_stream`) | △ (re-run model) | ✓ | ✓ | △ (session only) | ✗ |
| **Gradio** | ✓ | ✓ (yield) | △ | △ | ✓ | △ | ✗ |
| **Vite+React** | ✓ (fetch/SWR) | ✓ (SSE, EventSource) | ✓ | ✗ | ✓ | ✓ (WebSocket) | ✗ |
| **Next.js** | ✓ (Server Components + Actions) | ✓ (Streaming RSC) | ✓ (Actions, webhooks) | △ | ✓ | ✓ (WS/SSE) | △ (via ext cron) |
| **Expo (React Native)** | ✓ | ✓ | ✓ (notifications) | ✗ | ✓ | ✓ (WebSocket) | ✗ |
| **Astro Starlight** | ✗ (static docs) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **FastAPI** | ✓ (canonical) | ✓ (StreamingResponse) | ✓ (webhooks, BG tasks) | ✓ (BG tasks) | ✓ | ✓ (WebSocket) | ✓ (APScheduler) |
| **PocketBase** | ✓ (built-in REST) | ✓ (Realtime) | ✓ (hooks, Realtime) | △ | ✗ (no custom code) | ✓ (made for it) | ✗ |
| **Supabase Local** | ✓ (PostgREST) | ✓ (Realtime) | ✓ (Triggers, Edge Fns) | ✓ (Edge Fns) | ✓ (Edge Fns) | ✓ (made for it) | ✓ (pg_cron) |
| **Anthropic SDK** | ✓ | ✓ (`messages.stream`) | ✓ (tool_use) | ✓ | ✓ (canonical) | △ | ✓ |
| **SQLite / DuckDB / LanceDB** | pattern-neutral — used by any stack | | | | | | |

**Key Takeaways:**
- **FastAPI** and **Supabase Local** are the most versatile backends (support all patterns)
- **Streamlit/Gradio** are strong for Sync/Streaming/Pipeline/Agent, weak for Event/Real-time
- **Astro Starlight** is static-only — no patterns apply
- **PocketBase** is strong for CRUD/Realtime, weak for Agent/Batch (no custom code execution)

## The 7 Patterns

| Pattern | Core Idea | Domain Signal |
|---|---|---|
| [**Sync REST / CRUD**](sync-rest.md) | Request → Response | "user views list, edits items" |
| [**Streaming**](streaming.md) | Continuous output during production | "live updates", "as it happens", "progress" |
| [**Event-Driven**](event-driven.md) | Publisher fires → Subscribers react independently | "when X happens, then Y, Z, W" |
| [**Pipeline / ETL**](pipeline.md) | Data flows through sequential stages | "ingest → validate → transform → export" |
| [**Agent Loop**](agent-loop.md) | LLM decides next tool, iterates until done | "AI agent", "self-directed", "tool use" |
| [**Real-time / Collaborative**](real-time.md) | Shared state, multiple clients | "live collaborative", "shared editing" |
| [**Batch / Scheduled**](batch.md) | Periodic processing without user trigger | "nightly", "hourly", "cron", "scheduled" |

## Decision Signals — SPEC → Pattern

| If the SPEC says... | Pattern |
|---|---|
| "user views list, edits items", "CRUD", "admin panel" | [Sync REST / CRUD](sync-rest.md) (default) |
| "live", "streaming", "as it happens", "progress updates" | [Streaming](streaming.md) |
| "when X happens then Y", "notify", "trigger", "webhook", "on scan" | [Event-Driven](event-driven.md) |
| "process files", "transform", "N stages", "ingest → export" | [Pipeline / ETL](pipeline.md) |
| "AI agent", "research assistant", "self-directed", "tool use" | [Agent Loop](agent-loop.md) |
| "collaborative", "multi-user live", "shared editing", "kanban" | [Real-time](real-time.md) |
| "nightly", "hourly", "cron", "scheduled", "batch" | [Batch](batch.md) |

When in doubt → Sync REST / CRUD.

## Language in Code Examples

Each pattern file includes a Python code skeleton for concreteness. **Python is shown as an example — the pattern applies equally to TypeScript, JavaScript, Go, etc.** Check your stack's entry in the matrix above and its individual stack file for language-specific library names.

## Pattern Interaction

Most prototypes use **one primary pattern**. Occasionally two patterns combine:

- **Sync REST + Streaming**: REST endpoints, but one endpoint streams (e.g. `/api/chat` streams while `/api/history` is sync)
- **Sync REST + Batch**: CRUD app with a nightly job
- **Event-Driven + Sync REST**: REST endpoints fire events that trigger side effects
- **Agent Loop + Streaming**: agent iterates, but streams its intermediate thoughts

Avoid three+ patterns in one prototype. That's when you outgrow the archetype
and need a proper architecture design (not a greenfield scaffold).
