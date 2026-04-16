# Sync REST / CRUD (Default)

Request → handler → data access → response. The default pattern for ~80% of prototypes.

## When to Use

User-initiated actions with immediate response. Forms, admin panels, dashboards, standard APIs. The user clicks, waits briefly, sees result.

## Core Flow

```
request → router/handler → domain logic → data access → response
```

## Domain Signals

- "user views list, edits items"
- "CRUD", "admin panel"
- "form submission"
- "search + display"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python is shown for concreteness. The same pattern applies in TypeScript (Next.js Server Actions, Express routes), Go (net/http), etc. Check the matrix in the pattern README for your stack's idiom.

**FastAPI:**
```python
# app.py
@app.get("/items")
def list_items(db: Session = Depends(get_db)) -> list[ItemOut]:
    items = get_active_items(db)       # data.py
    return [ItemOut.from_orm(i) for i in items]

@app.post("/items")
def create_item(body: ItemIn, db: Session = Depends(get_db)) -> ItemOut:
    validated = validate_item(body)    # domain.py
    item = insert_item(db, validated)  # data.py
    return ItemOut.from_orm(item)
```

**Streamlit:**
```python
# app.py
uploaded = st.file_uploader("CSV")
if uploaded:
    df = load_and_validate(uploaded)   # data.py
    stats = compute_stats(df)           # domain.py
    render_dashboard(df, stats)         # app.py
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| FastAPI | Route decorators + Pydantic request/response models |
| Flask / Django | Standard MVC-style views |
| Next.js | Server Components + Server Actions |
| Vite+React | fetch / SWR / TanStack Query on top of FastAPI endpoints |
| Streamlit | Top-level script, `st.*` widgets trigger re-runs |
| Gradio | `gr.Interface(fn=...)` |
| PocketBase | Built-in REST API generated from collections |
| Supabase Local | PostgREST auto-generated from Postgres schema |

## Anti-Patterns

- **Don't use for long-running operations (>5s)** — use Streaming or Batch
- **Don't embed business logic in route handlers** — push to domain module
- **Don't poll for updates** — use Streaming or Real-time instead
- **Don't couple the DB schema to the API response shape** — validate/transform via Pydantic DTOs
