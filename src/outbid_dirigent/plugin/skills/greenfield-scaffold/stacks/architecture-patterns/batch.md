# Batch / Scheduled

Scheduler triggers → process all pending work → write results → log.

## When to Use

Periodic work without user interaction. Reports, sync jobs, cleanup tasks, data imports, analytics aggregations.

Key trait: **no user waits for this**. It runs on a schedule and logs its results.

## Core Flow

```
scheduler fires (cron / every N min) → collect work → process → persist → log
```

## Domain Signals

- "nightly", "hourly", "daily"
- "cron", "scheduled"
- "batch", "periodic"
- "backfill", "sync", "cleanup"
- "send weekly report"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for the APScheduler example. TypeScript/Node would use `node-cron` or external triggers (Vercel Cron, GitHub Actions).

**APScheduler (in-process, with FastAPI):**
```python
# app.py
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from fastapi import FastAPI

def nightly_report() -> None:
    data = collect_metrics()        # data.py
    report = render_report(data)    # domain.py
    save_report(report)             # data.py
    logger.info(f"Nightly report saved: {len(data)} rows")

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(nightly_report, "cron", hour=2, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

**Supabase pg_cron (DB-level):**
```sql
SELECT cron.schedule(
    'nightly-cleanup',
    '0 2 * * *',
    $$DELETE FROM sessions WHERE expires_at < now()$$
);

SELECT cron.schedule(
    'hourly-aggregate',
    '0 * * * *',
    $$SELECT refresh_materialized_view('visit_stats')$$
);
```

**External trigger (GitHub Actions → HTTP):**
```yaml
# .github/workflows/nightly.yml
on:
  schedule:
    - cron: '0 2 * * *'
jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - run: curl -X POST ${{ secrets.APP_URL }}/jobs/nightly
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| FastAPI | `APScheduler` (in-process) or external cron hitting an endpoint |
| Supabase Local | `pg_cron` extension — schedules run inside Postgres |
| Anthropic SDK | Any of the above, calling `messages.create()` in the job |
| Next.js | Vercel Cron or external trigger to API route |

**Avoid for prototypes:** Celery, Airflow — too much infrastructure.

## Anti-Patterns

- **Don't skip idempotency** — jobs will re-run (manual retries, overlapping schedules); they MUST be safe to re-run
- **Don't silently fail** — log errors and alert (at minimum: write to a monitoring table)
- **Don't do long work on the main process without locks** — two overlapping runs corrupt state; use a flag / advisory lock
- **Don't embed scheduling in user-facing endpoints** — separate scheduled jobs from request handlers
- **Don't skip logging start/end times and row counts** — you need this to debug when a job "succeeds" but produces zero output
