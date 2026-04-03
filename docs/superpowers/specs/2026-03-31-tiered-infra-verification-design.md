# Tiered Infrastructure & Verification Confidence

**Date**: 2026-03-31
**Status**: Approved for implementation planning
**Scope**: `init_phase.py`, `infra_schema.py` (new), `contract_schema.py`, `shipper.py`, `router.py`, `test_harness_schema.py`

---

## Problem

Tests frequently cannot run because required services (databases, queues, dev server) are absent or misconfigured. The current `init_phase.py` looks for an `init.sh` script, falls back to a skill invocation, but never programmatically detects or provisions services. As a result:

- The contract review loop signs off on phases without live behavioral evidence
- Tests either don't run or pass vacuously (no seed data, no services)
- There is no signal in the PR or portal about what was actually verified

Hard-blocking runs on missing infra is not acceptable — it kills the autonomous flow. The solution is to **annotate what was verified and at what confidence**, never to stop a run.

---

## Design Principles

- Runs never block due to missing infra — they proceed at lower confidence
- Every test result carries a confidence level that reflects what actually ran
- Missing infra generates setup tasks inside the plan, not a pre-flight error
- The system learns from past runs via ruflo memory — cold-start safe

---

## Section 1 — Verification Confidence Levels

A `confidence` field is added to every contract `Review`. It is set by the infra tier that was active during execution and cannot be manually overridden.

| Confidence | Meaning |
|---|---|
| `e2e` | Full e2e suite ran against a running app |
| `integration` | Integration tests ran against live services |
| `unit` | Unit tests ran; no external services needed |
| `mocked` | Tests ran against in-process fakes/mocks |
| `static` | No tests ran; structural inspection only |
| `none` | No test suite found |

The existing `PASS / FAIL` verdict is preserved unchanged. `confidence` is additive. A PASS at `static` confidence is valid — it just means less was verified.

The contract quality override logic (`unproven criteria → override PASS to FAIL`) remains but becomes tier-aware: criteria verified at `mocked` or above are considered to have evidence.

---

## Section 2 — Tiered InfraDetector

A new `InfraDetector` class in `init_phase.py` runs before any init script check and before planning. It probes in priority order and stops at the first viable tier.

### Environment tiers (what runs the code)

| Tier | Mechanism | Detection signal |
|---|---|---|
| 1 | Devbox | `devbox version` exits 0 AND `devbox.json` exists |
| 2 | asdf / mise | `.tool-versions` exists |
| 3 | Native | PATH contains required runtime (node, python, etc.) |

### Services tiers (what the code connects to)

| Tier | Mechanism | Detection signal | Action |
|---|---|---|---|
| `1_devbox` | Devbox services (process-compose) | `devbox.json` contains known service packages (postgresql, redis, mysql) | `devbox services start <svc>` |
| `2_docker_compose` | docker-compose | `docker-compose.yml` or `compose.yml` exists AND `docker info` exits 0 | `docker compose up -d` |
| `3_ci_extracted` | GitHub Actions services block | `.github/workflows/*.yml` parsed for `jobs.*.services` | Reconstruct connection strings; generate local compose.yml from CI spec |
| `4_mocked` | In-process fakes | Test imports contain `fakeredis`, `sqlite:///:memory:`, `mongomock`, etc. | No action needed; note in InfraContext |
| `5_generated_devbox` | Generate devbox.json | devbox viable but no devbox.json; stack detected from package.json / requirements.txt / go.mod | Write `devbox.json` from stack template |
| `6_generated_compose` | Generate docker-compose.yml | devbox not viable; services needed; Docker available | Write `docker-compose.yml` from detected services |
| `7_none` | Comment | Neither viable nor generatable | Populate `InfraContext.gaps`; proceed at `static` confidence |

### Devbox detection note

`which devbox` is insufficient — nix must also be in PATH. Always run `devbox version 2>/dev/null` and check exit code.

### Postgres devbox note

Before `devbox services start postgresql`, an `initdb` call is required. The generated `devbox.json` must include this in `shell.init_hook`.

### Seed data detection

After services start, `InfraDetector` runs seed detection:

| Signal | Command | Detection confidence |
|---|---|---|
| `prisma/seed.ts` or `prisma/seed.js` exists | `npx prisma db seed` | high |
| `package.json` has `db:seed` / `seed` script | `npm run db:seed` | high |
| `db/seeds.rb` exists | `rails db:seed` | high |
| `seeds/` directory with `.js`/`.ts` | `npx knex seed:run` | medium |
| Django `fixtures/*.json` | `python manage.py loaddata <file>` | medium |
| `conftest.py` uses `sqlite:///:memory:` | no seed needed | high |
| Nothing found | — | none |

Seed failure is non-blocking. It reduces confidence from `integration` to `mocked`.

### Output: InfraContext

`InfraDetector` produces an `InfraContext` (Pydantic model, see Section 5) written to `.dirigent/infra-context.json`. All downstream components read from this file — nothing re-probes.

The existing `RuntimeAnalysis.uses_docker_compose` and `RuntimeAnalysis.services` in `analyzer.py` are read by `InfraDetector` rather than re-detected.

---

## Section 3 — Confidence Flow into Contracts, PR, and Portal

### Contract review

`CriterionResult` in `contract_schema.py` gains a `verification_tier` field (the infra tier string). The reviewer is instructed to use the highest tier of evidence available per criterion.

`Review` gains two new fields:

```python
confidence: str          # e2e | integration | unit | mocked | static | none
infra_tier: str          # mirrors InfraTier value
tests_run: int = 0
tests_skipped_infra: int = 0
caveat: str = ""         # human-readable explanation of what wasn't verified
```

### PR description (shipper.py)

A `## Verification` section is prepended to every PR body:

```
## Verification
✅ Tests passed — integration confidence (docker-compose)
   47 tests run, 0 skipped

   or

✅ Tests passed — mocked confidence (fakeredis)
⚠️  12 integration tests skipped — real Redis not available
   To verify at integration confidence: docker compose up redis && npm test
```

When gaps exist, a checklist from `InfraContext.gaps` is appended so the human reviewer knows exactly what to run.

### Portal

`confidence` and `infra_tier` are added to the existing `stage_complete("testing", ...)` reporter call. No schema changes to the portal API — they are additional fields in the `details` dict.

---

## Section 4 — Ruflo Learning Layer

After each run completes, results are persisted to ruflo memory under namespace `dirigent-infra`. The key is a stack fingerprint: `{framework}+{primary_service}` (e.g. `nextjs+postgres`).

**Stored per run:**
- Infra tier that succeeded and time-to-ready
- Seed command used and its confidence
- Which behavioral criteria needed live infra vs. ran mocked
- CI service block → connection string mappings observed

**At the start of each run**, `InfraDetector` queries ruflo before probing:

```python
results = memory_search(
    query=f"{framework}+{primary_service} infra tier seed command",
    namespace="dirigent-infra",
    limit=3,
)
```

A high-confidence match skips lower tiers and goes directly to the known-working tier.

**Contract generator** queries ruflo for proven criteria patterns before writing a new contract:

```python
results = memory_search(
    query=f"{framework} behavioral criteria verification patterns",
    namespace="dirigent-contracts",
)
```

**Cold-start safe**: if ruflo is empty (no prior runs), `InfraDetector` falls through the full tier probe sequence as today. The learning layer is purely additive.

---

## Section 5 — Schema Hygiene

### New file: `infra_schema.py`

```python
class InfraTier(str, Enum):
    DEVBOX = "1_devbox"
    DOCKER_COMPOSE = "2_docker_compose"
    CI_EXTRACTED = "3_ci_extracted"
    MOCKED = "4_mocked"
    GENERATED_DEVBOX = "5_generated_devbox"
    GENERATED_COMPOSE = "6_generated_compose"
    NONE = "7_none"

class ServiceGap(BaseModel):
    service: str
    port: Optional[int]
    reason: str
    suggested_fix: str

class SeedInfo(BaseModel):
    command: str = ""
    detection_confidence: str = "none"   # high | medium | none — how reliably the seed command was detected
    ran: bool = False
    error: str = ""

class InfraContext(BaseModel):
    tier: InfraTier = InfraTier.NONE
    services_started: list[str] = []
    confidence: str = "static"
    gaps: list[ServiceGap] = []
    seed: SeedInfo = SeedInfo()
    generated_files: list[str] = []

    @classmethod
    def load(cls, path: Path) -> "InfraContext | None": ...
    def save(self, path: Path): ...
```

Written to `.dirigent/infra-context.json`. Replaces ad-hoc gap dicts.

### Retrofit: `ROUTE.json` and `STATE.json`

Both files have stable, consistent shapes. Wrap in Pydantic models in `router.py`:

```python
class RouteRecord(BaseModel):
    route: str
    reason: str
    steps: list[str]
    step_details: list[dict]
    estimated_tasks: int
    oracle_needed: bool
    repo_context_needed: bool
    created_at: str

class StateRecord(BaseModel):
    completed_steps: list[str]
    started_at: str
    updated_at: str
```

`load_route()` and `load_state()` use `model_validate()` internally. Return types become typed. Callers don't change. Corrupt files raise `ValidationError` with a clear message instead of a silent `KeyError`.

### Leave as-is

`DECISIONS.json` and `ANALYSIS.json` remain plain dicts — they are append-only caches read only for prompt context injection. Validation overhead is not justified.

---

## Files Changed

| File | Change |
|---|---|
| `src/outbid_dirigent/infra_schema.py` | New — `InfraTier`, `ServiceGap`, `SeedInfo`, `InfraContext` |
| `src/outbid_dirigent/init_phase.py` | Add `InfraDetector` class; write `infra-context.json` |
| `src/outbid_dirigent/contract_schema.py` | Add `confidence`, `infra_tier`, `tests_run`, `tests_skipped_infra`, `caveat` to `Review`; add `verification_tier` to `CriterionResult` |
| `src/outbid_dirigent/shipper.py` | Add `## Verification` section to PR body from `InfraContext` |
| `src/outbid_dirigent/router.py` | Wrap `ROUTE.json` / `STATE.json` in `RouteRecord` / `StateRecord` |
| `src/outbid_dirigent/test_harness_schema.py` | Add `infra_tier` field |
| `src/outbid_dirigent/executor.py` | Pass `InfraContext` through to contract manager and reporter |
| `src/outbid_dirigent/portal_reporter.py` | Include `confidence` + `infra_tier` in testing stage events |

---

## Out of Scope

- Changing the routing algorithm or route types
- Parallelising task execution
- Changes to the Oracle
- Portal API schema changes (confidence flows as extra fields in existing events)
