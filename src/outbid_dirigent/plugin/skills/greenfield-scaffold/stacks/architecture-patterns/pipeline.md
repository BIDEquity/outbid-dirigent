# Pipeline / ETL

Input → stage_1 → stage_2 → ... → stage_N → output. Data flows through sequential transformation stages.

## When to Use

Data transformation with distinct phases. Each stage has a clear input and output contract.

Classic example: "Read CSVs → validate schema → transform columns → aggregate → write Parquet". Four stages, each doing one thing.

## Core Flow

```
input → stage_1(input) → stage_2(out_1) → stage_3(out_2) → ... → output
```

## Domain Signals

- "process files"
- "transform"
- "N stages", "multi-step"
- "ingest → export"
- "ETL", "data pipeline"

## Code Example (Python — adapt to your stack's language)

> **Language note:** Python shown for concreteness, and it's a natural fit because of `polars` / `pandas`. TypeScript would use similar function composition; the pattern is the same.

**Plain Python functions (prototype-grade):**
```python
# pipeline.py
from pathlib import Path
import polars as pl

def ingest(source: Path) -> pl.DataFrame:
    return pl.read_csv(source)

def validate(df: pl.DataFrame) -> pl.DataFrame:
    required = {"customer_id", "amount", "date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    return df.drop_nulls(subset=list(required))

def transform(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns([
        pl.col("amount").cast(pl.Float64),
        pl.col("date").str.to_date(),
    ])

def aggregate(df: pl.DataFrame) -> pl.DataFrame:
    return df.group_by("customer_id").agg(pl.col("amount").sum())

def export(df: pl.DataFrame, dest: Path) -> None:
    df.write_parquet(dest)

# app.py
def run_pipeline(source: Path, dest: Path) -> None:
    df = ingest(source)
    df = validate(df)
    df = transform(df)
    df = aggregate(df)
    export(df, dest)
```

**FastAPI background task:**
```python
# app.py
@app.post("/pipeline/run")
def trigger_pipeline(body: PipelineRequest, bg: BackgroundTasks):
    bg.add_task(run_pipeline, Path(body.source), Path(body.dest))
    return {"status": "started"}
```

## Libraries by Stack

| Stack | Idiom |
|---|---|
| Python | Plain functions + `polars` (preferred) or `pandas` |
| FastAPI | `BackgroundTasks` for async pipelines |
| Supabase | Edge Functions for transformations, pg_cron for scheduling |
| Streamlit | Top-level script with sequential function calls |

**Avoid for prototypes:** Prefect, Dagster, Airflow — too much infrastructure for a pipeline of 4 stages.

## Anti-Patterns

- **Don't hide stages inside classes** — flat functions are easier to test and swap
- **Don't skip explicit types on stage I/O** — they ARE the contract between stages
- **Don't mutate between stages** — return new data structures
- **Don't mix pipeline logic with presentation** — pipeline is headless; UI is separate
- **Don't skip logging/checkpoints** — pipelines fail halfway, you need to know where
