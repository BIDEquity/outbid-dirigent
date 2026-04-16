# Stack Reference — Greenfield Scaffold

Opinionated defaults for rapid prototyping. The agent does NOT deliberate over stack choices — it matches the SPEC shape to an archetype and picks the combo.

## Tooling Conventions

These are non-negotiable. Don't deliberate, don't pick alternatives.

- **Python projects**: Use `uv`. Not pip, not poetry, not pipenv. `uv init`, `uv add`, `uv run`, `uv sync`. Query context7 for `uv` docs.
- **Node projects**: Use `npm`/`npx`. `--` separates npm args from script args. Query context7 for current framework CLI flags.
- **E2E testing**: Playwright for web. Query context7 for `playwright` setup and API.
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
| Next.js components | Server Components by default, `"use client"` only for interactivity | `"use client"` on every file |
| Next.js data fetching | server components + `fetch` | React Query / TanStack Query in Next.js |
| Forms | native `FormData` + server actions (Next.js), `useState` (Vite) | React Hook Form for a 3-field form |
| State management | `useState` + `useContext` | Redux, Zustand for prototypes |
| CSS/Styling | Tailwind if scaffold includes it, otherwise CSS modules | styled-components, emotion |

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
| ORM | skip for prototypes. Raw SQL or `sqlmodel` if you must. |
| API style | REST. Not GraphQL. Not tRPC. |
| Auth | don't build it. PocketBase or Supabase handle it. |
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

## Archetype Combos

Match the SPEC to one of these archetypes. Pick the first one that fits.

### Web Apps

| SPEC Shape | Combo | Ports |
|---|---|---|
| "Dashboard for this data" | Streamlit + DuckDB | 8501 |
| "API + frontend app" | FastAPI + Vite+React | 8000, 5173 |
| "Full-stack app with auth" (simple) | Next.js + PocketBase | 3000, 8090 |
| "Full-stack app with auth" (production) | Next.js + Supabase Local | 3000, 54321, 54323 |
| "App with database" | FastAPI + SQLite | 8000 |
| "Internal tool / form app" | Streamlit | 8501 |
| "Docs site / landing page" | Astro Starlight | 4321 |
| "Python app with real database" | FastAPI + Supabase Local | 8000, 54321 |
| "Data pipeline + dashboard" | Streamlit + DuckDB + FastAPI | 8501, 8000 |

### AI Apps

| SPEC Shape | Combo | Ports |
|---|---|---|
| "Chatbot / AI assistant" | Streamlit + Anthropic SDK | 8501 |
| "Document Q&A / search" | Streamlit + LanceDB + Anthropic SDK | 8501 |
| "AI agent with tools" | FastAPI + Anthropic SDK | 8000 |
| "AI-powered data analysis" | Streamlit + DuckDB + Anthropic SDK | 8501 |
| "ML model demo" | Gradio | 7860 |

### Mobile Apps

| SPEC Shape | Combo | Ports |
|---|---|---|
| "Mobile app" (simple) | Expo + PocketBase | 8081, 8090 |
| "Mobile app" (production) | Expo + Supabase Local | 8081, 54321, 54323 |
| "Mobile app with scanning/camera/NFC" | Expo + Supabase Local + expo-camera | 8081, 54321, 54323 |

### Default

| SPEC Shape | Combo | Ports |
|---|---|---|
| Default (unclear) | Streamlit | 8501 |

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
