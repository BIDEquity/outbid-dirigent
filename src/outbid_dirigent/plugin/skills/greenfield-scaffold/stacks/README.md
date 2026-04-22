# Stack Reference — Greenfield Scaffold

Opinionated defaults for rapid prototyping. The agent does NOT deliberate over stack choices — it matches the SPEC shape to an archetype and picks the combo.

## Tooling Conventions

These are non-negotiable. Don't deliberate, don't pick alternatives.

- **Python projects**: Use `uv`. Not pip, not poetry, not pipenv. `uv init`, `uv add`, `uv run`, `uv sync`. Query context7 for `uv` docs.
- **Node projects**: Use `npm`/`npx`. `--` separates npm args from script args. Query context7 for current framework CLI flags.
- **E2E testing (web archetypes)**: Install Playwright unconditionally — the install command is stable, no context7 lookup required:
  ```bash
  npm install -D @playwright/test
  npx playwright install --with-deps chromium
  ```
  Write `e2e_framework` into `test-harness.json` so downstream contract negotiators see it. Use context7 _only_ for API/syntax recall when writing the first spec — missing context7 is NOT a reason to skip the install.
- **Process orchestration**: Start servers with `&`, wait with `curl --retry-connrefused --retry 5 http://localhost:PORT/health`, then test.
- **Port conflicts**: `lsof -i :PORT` to find, `kill -9 <PID>` to clear.
- **Secrets**: `.env` files, never committed. Frameworks load them automatically.

## Opinionated Defaults

These apply to ALL greenfield projects. The agent follows these — no exceptions, no "I think it would be better to..."

### Python

| What | Use | NOT |
|---|---|---|
| Package management | `uv` | pip, poetry, pipenv |
| DataFrames | `polars` | pandas |
| Validation / API I/O | `pydantic` | manual dict parsing, marshmallow, attrs |
| Config | `pydantic-settings` (reads `.env`, typed) | `os.environ`, python-dotenv scattered |
| Internal data objects | `dataclasses` | pydantic for internal-only structs |
| HTTP client | `httpx` | requests, aiohttp |
| Logging | `loguru` | stdlib logging with handlers/formatters |
| CLI apps | `typer` | argparse, click |
| Path handling | `pathlib.Path` | `os.path` |
| JSON | stdlib `json` (add `orjson` only if perf matters) | msgpack, protobuf |
| Testing | plain `pytest` functions + fixtures | `unittest.TestCase`, setUp/tearDown |
| Temp files in tests | `tmp_path` fixture | manual `os.makedirs` + `try/finally` |
| Formatting | `ruff format` | black, autopep8, isort |
| Async | only if the framework wants it (FastAPI = yes) | celery + redis for one background task |
| Date/time | `datetime` with `timezone.utc`, always UTC | naive datetimes, pytz |

### JavaScript / TypeScript

| What | Use | NOT |
|---|---|---|
| Language | TypeScript, always | plain JavaScript |
| HTTP client | native `fetch` (built-in since Node 18) | axios |
| UUID | `crypto.randomUUID()` | uuid package |
| Validation | `zod` (runtime + TS inference) | manual `if (!data.field)` checks, joi, yup |
| Clone/copy | `structuredClone()` | lodash |
| Date/time | native `Date`, `Intl.DateTimeFormat` | moment.js, dayjs |
| Formatting | whatever the scaffold ships | adding prettier separately |
| Exports | named exports | default exports, barrel files (`index.ts` re-exporting) |
| CSS/Styling | Tailwind (Next.js scaffold includes it via `--tailwind`) | styled-components, emotion, plain CSS |
| ORM (JS) | `prisma` (when raw SQL gets tedious) | TypeORM, Sequelize, Drizzle |
| Next.js components | Server Components by default, `"use client"` only for interactivity | `"use client"` on every file |
| Next.js data fetching | server components + `fetch` | React Query / TanStack Query in Next.js |
| Forms | native `FormData` + server actions (Next.js), `useState` (Vite) | React Hook Form for a 3-field form |
| State management | `useState` + `useContext` | Redux, Zustand for prototypes |

### AI Integration

| What | Use | NOT |
|---|---|---|
| LLM SDK | `anthropic` directly | LangChain, LlamaIndex, CrewAI, AutoGen |
| Structured output | `client.messages.parse()` + Pydantic | parsing JSON from free text, regex |
| Streaming (UI) | `client.messages.stream()` — always when user waits | non-streaming (30s blank screen) |
| Prompt caching | always for repeated system prompts | re-sending full context every call |
| RAG (keyword) | DuckDB FTS or SQLite FTS | ChromaDB for simple keyword search |
| RAG (semantic) | `lancedb` (embedded, local) | Pinecone, Weaviate (cloud) |
| Embeddings (local) | `sentence-transformers` | — |
| Embeddings (API) | Voyage AI | OpenAI embeddings |
| Agent framework | raw SDK + tool use | LangChain agents |
| API keys | `.env` → `pydantic-settings` | hardcoded, `os.environ` scattered |
| Cost tracking | log `response.usage` tokens | ignore costs |
| Rate limits | `tenacity` with exponential backoff | bare `try/except/sleep` |
| Local LLM | Ollama (only if SPEC requires it) | manual GGUF loading |

### Architecture

| What | Rule |
|---|---|
| Abstractions | none until 2+ implementations. No DI frameworks. No event bus. |
| File nesting | max 2 levels deep. Flat > nested. |
| Barrel files | don't create `index.ts` re-exporting everything |
| ORM (Python) | `sqlmodel` when raw SQL gets tedious. Not SQLAlchemy + Alembic for prototypes. |
| ORM (JS) | `prisma` when raw SQL gets tedious. Not TypeORM, Sequelize. |
| API style | REST. Not GraphQL. Not tRPC. |
| Auth | don't build it. PocketBase (local, lightweight) or Supabase Local (local, production-grade). Skip OAuth/SSO for prototypes — email+password is enough. |
| File storage | use the backend's built-in: Supabase Storage or PocketBase file fields. Not a separate S3/MinIO for prototypes. |
| NoSQL / documents | use Postgres JSONB (via Supabase) or DuckDB nested types. Not MongoDB for prototypes. |
| Event-driven | don't for prototypes. Direct function calls. If you must: FastAPI BackgroundTasks or simple in-process callbacks. Not Kafka, RabbitMQ, Redis Pub/Sub. |
| CSS | Tailwind (comes with Next.js scaffold). For Python UIs: Streamlit handles it. Don't add CSS frameworks to Streamlit/Gradio apps. |
| CORS (prototype) | `allow_origins=["*"]` is fine. Note "tighten for prod" in start.sh. |
| Monorepo | no. One repo, one project. |
| Dependencies | fewer is better. Don't add a lib for what stdlib does. |
| Error handling | let it crash. Don't catch-all. Validate at boundaries only. |
| Don't add yet | no Dockerfile (except for Supabase), no CI/CD, no monitoring, no i18n, no Sentry |

## Tier Table

| Role | Tier 1 (Default) | Tier 2 (When T1 Doesn't Fit) |
|---|---|---|
| Python UI | [Streamlit](streamlit.md) | NiceGUI |
| JS Frontend | [Vite+React](vite-react.md) | SvelteKit |
| Full-stack JS | [Next.js](nextjs.md) | — |
| Python Backend | [FastAPI](fastapi.md) | Django |
| Backend + Auth (lightweight) | [PocketBase](pocketbase.md) | — |
| Backend + Auth (production) | [Supabase Local](supabase-local.md) | — |
| Database (OLTP) | [SQLite](sqlite.md) | Postgres (via Supabase) |
| Database (Analytics) | [DuckDB](duckdb.md) | — |
| ML/Model UI | [Gradio](gradio.md) | Streamlit |
| Docs/Static | [Astro Starlight](astro-starlight.md) | — |
| Mobile | [Expo](expo.md) | — |
| LLM Integration | [Anthropic SDK](anthropic-sdk.md) | — |
| Vector DB / RAG | [LanceDB](lancedb.md) | — |

## Choosing Stack × Architecture

Every greenfield scaffold picks from **four dimensions** in the SPEC:

1. **Stack** (Use-Case-Archetype) → which stack combo (tables below)
2. **Interaction Shape** → Sync REST / Streaming / Event-Driven / Real-time / Batch
3. **Compute Topology** → In-Process / Serverless / Long-running Worker
4. **Domain Pattern** (optional) → Pipeline / Agent Loop / State Machine / Webhook Receiver / Multi-Tenant

See **[architecture-patterns/](architecture-patterns/README.md)** for all three architecture axes with decision signals and matrices.

**Check the Stack × Interaction Shape Matrix BEFORE committing to a combo** — some combos don't fit (e.g. Streamlit + Real-time = △, Astro Starlight + anything dynamic = ✗).

Default: **Sync REST + In-Process + (no Domain Pattern)** — covers ~80% of prototypes. Only deviate when the SPEC explicitly demands otherwise.

## Archetype Combos

Match the SPEC to one of these archetypes. Pick the first one that fits.
"Typical Pattern" is the default for that archetype — can be overridden if SPEC demands.

### Web Apps

| SPEC Shape | Combo | Ports | Typical Pattern |
|---|---|---|---|
| "Dashboard for CSV data" | Streamlit + DuckDB | 8501 | Sync REST |
| "Live dashboard for sensor data" | Streamlit + DuckDB | 8501 | Streaming |
| "API + frontend app" | FastAPI + Vite+React | 8000, 5173 | Sync REST |
| "Event-driven workflow API" | FastAPI + Supabase Local | 8000, 54321 | Event-Driven |
| "ETL pipeline" | FastAPI + DuckDB | 8000 | Pipeline / ETL |
| "Scheduled report generator" | FastAPI + SQLite | 8000 | Batch |
| "Full-stack app with auth" (simple) | Next.js + PocketBase | 3000, 8090 | Sync REST |
| "Full-stack app with auth" (production) | Next.js + Supabase Local | 3000, 54321, 54323 | Sync REST |
| "Collaborative whiteboard" | Next.js + Supabase Local | 3000, 54321 | Real-time |
| "App with database" | FastAPI + SQLite | 8000 | Sync REST |
| "Internal tool / form app" | Streamlit | 8501 | Sync REST |
| "Docs site / landing page" | Astro Starlight | 4321 | — (static) |
| "Python app with real database" | FastAPI + Supabase Local | 8000, 54321 | Sync REST |
| "Data pipeline + dashboard" | Streamlit + DuckDB + FastAPI | 8501, 8000 | Pipeline / ETL |

### AI Apps

| SPEC Shape | Combo | Ports | Typical Pattern |
|---|---|---|---|
| "Chatbot / AI assistant" | Streamlit + Anthropic SDK | 8501 | Streaming |
| "Document Q&A / search" | Streamlit + LanceDB + Anthropic SDK | 8501 | Streaming |
| "AI agent with tools" | FastAPI + Anthropic SDK | 8000 | Agent Loop |
| "AI-powered data analysis" | Streamlit + DuckDB + Anthropic SDK | 8501 | Agent Loop |
| "ML model demo" | Gradio | 7860 | Sync REST |

### Mobile Apps

| SPEC Shape | Combo | Ports | Typical Pattern |
|---|---|---|---|
| "Mobile app" (simple) | Expo + PocketBase | 8081, 8090 | Sync REST |
| "Mobile app" (production) | Expo + Supabase Local | 8081, 54321, 54323 | Sync REST |
| "Mobile app with scanning/camera/NFC" | Expo + Supabase Local + expo-camera | 8081, 54321, 54323 | Event-Driven |
| "Real-time collaborative mobile" | Expo + Supabase Local | 8081, 54321 | Real-time |

### Default

| SPEC Shape | Combo | Ports | Typical Pattern |
|---|---|---|---|
| Default (unclear) | Streamlit | 8501 | Sync REST |

## Each Stack File Contains

1. **Docs** — context7 query for up-to-date documentation
2. **Check Installation** — commands to verify the tool is available
3. **Scaffold** — exact commands to create the project skeleton
4. **Run** — how to start the app (command + port)
5. **Test** — how to test it (framework, example test, run command)
6. **Start Script Pattern** — the `start.sh` template for shipping
7. **Pairing** — what it combines well with

## How This Feeds Downstream

- **Contract creation** → test commands from each stack file become acceptance criteria
- **Execution** → scaffold commands become the first task; opinionated defaults constrain library choices
- **Shipping** → start script patterns become `start.sh` in the delivered repo
