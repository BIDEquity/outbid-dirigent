# Outbid Dirigent — Architecture Manifest

> Headless autonomous coding agent controller. Reads a SPEC.md, analyzes the target repo, selects an execution route, creates a phased plan, and runs each task through Claude Code with atomic commits and automatic error recovery.

## System Overview

```mermaid
graph TB
    SPEC["📄 SPEC.md"] --> DIRIGENT
    REPO["📁 Target Repo"] --> DIRIGENT

    subgraph DIRIGENT["Dirigent Control Plane"]
        direction TB
        AN[Analyzer] --> RT[Router]
        RT --> EX[Executor]
        EX --> PL[Planner]
        EX --> TR[TaskRunner]
        EX --> SH[Shipper]
        EX --> IP[InitPhase]
        EX --> OR[Oracle]
    end

    TR -->|subprocess| CC["Claude Code CLI"]
    OR -->|API| CLAUDE["Claude API"]
    SH -->|CLI| GH["GitHub (gh)"]
    EX -->|events| PORTAL["Outbid Portal"]
    EX -->|state| STATE[".dirigent/"]
```

## Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Dirigent as dirigent.py
    participant Analyzer
    participant Router
    participant Executor
    participant Planner
    participant TaskRunner
    participant CC as Claude Code
    participant Shipper
    participant Portal

    User->>Dirigent: --spec SPEC.md --repo /path
    Dirigent->>Analyzer: analyze(repo, spec)
    Analyzer-->>Dirigent: AnalysisResult (language, framework, route)
    Dirigent->>Router: determine_route(analysis)
    Router-->>Dirigent: Route (type + steps)
    Dirigent->>Portal: stage_start("execution")

    loop Each Step in Route
        Dirigent->>Executor: run_step(step)

        alt INIT
            Executor->>CC: run init.sh / seed data
            CC-->>Executor: test-harness.json
        else PLANNING
            Executor->>Planner: create_plan()
            Planner->>CC: /dirigent:create-plan
            CC-->>Planner: PLAN.json
        else EXECUTION
            loop Each Task in PLAN.json
                Executor->>TaskRunner: execute_task(task)
                TaskRunner->>CC: subprocess (fresh context)
                CC-->>TaskRunner: TaskResult (commit, deviations)
                TaskRunner->>Portal: task_result
            end
        else ENTROPY_MINIMIZATION
            Executor->>CC: /dirigent:entropy-minimization
            CC-->>Executor: entropy-report.json
        else SHIP
            Executor->>Shipper: ship()
            Shipper->>GH: branch + push + PR
        end
    end

    Dirigent->>Portal: stage_complete
    Dirigent-->>User: PR URL
```

## Route Selection

The Router selects one of five execution routes based on repo analysis and spec keywords:

```mermaid
flowchart LR
    A[AnalysisResult] --> D{Route Decision}

    D -->|"add, build, create"| G["GREENFIELD"]
    D -->|"refactor, migrate, rewrite"| L["LEGACY"]
    D -->|"complex existing + new feature"| H["HYBRID"]
    D -->|"test, coverage, testability"| T["TESTABILITY"]
    D -->|"analytics, tracking, events"| K["TRACKING"]

    G --> G1["Init → Plan → Execute → Entropy Min → Test → Ship"]
    L --> L1["Init → Extract Rules → Plan → Execute → Entropy Min → Test → Ship"]
    H --> H1["Init → Quick Scan → Plan → Execute → Entropy Min → Test → Ship"]
    T --> T1["Init → Testability Analysis → Plan → Execute → Entropy Min → Test → Ship"]
    K --> K1["Init → Quick Scan → PostHog Setup → Plan → Execute → Entropy Min → Test → Ship"]
```

## Module Architecture

```mermaid
graph LR
    subgraph Core["Core Orchestration"]
        dirigent.py
        analyzer.py
        router.py
        executor.py
        oracle.py
    end

    subgraph Execution["Task Execution"]
        task_runner.py
        planner.py
        shipper.py
    end

    subgraph Init["Init & Testing"]
        init_phase.py
        test_manifest.py
        test_harness_schema.py
    end

    subgraph Quality["Quality & Contracts"]
        contract.py
        contract_schema.py
        progress.py
    end

    subgraph Integration["Integrations"]
        portal_reporter.py
        questioner.py
        proteus_integration.py
        demo_runner.py
    end

    subgraph Infra["Infrastructure"]
        logger.py
        plan_schema.py
    end

    Core --> Execution
    Core --> Init
    Core --> Quality
    Core --> Integration
    Core --> Infra
```

## Contract → Execute → Review Loop

Each phase goes through a strict contract-based verification cycle. The agent cannot declare success without evidence.

```mermaid
flowchart TD
    START["Phase N begins"] --> CONTRACT["Create Contract\n(acceptance criteria with\nexecutable verification commands)"]
    CONTRACT --> EXECUTE["Execute all tasks\nin phase"]
    EXECUTE --> REVIEW["Reviewer subprocess:\n1. Read contract criteria\n2. Run verification commands\n3. Record evidence (command + output)\n4. PASS/FAIL verdict"]

    REVIEW --> CHECK{Verdict?}
    CHECK -->|PASS with evidence| NEXT["Phase N+1"]
    CHECK -->|PASS without evidence| OVERRIDE["Orchestrator overrides\nto FAIL (no proof)"]
    CHECK -->|FAIL| FIX["Executor subprocess:\nFix critical + warn findings"]
    CHECK -->|ERROR x2| HALT["HALT execution"]

    OVERRIDE --> FIX
    FIX --> REVIEW
    FIX -->|max 3 iterations| HALT

    HALT["HALT\n(--resume to retry)"]

    style HALT fill:#ff4444,color:#fff
    style OVERRIDE fill:#ff8800,color:#fff
    style NEXT fill:#44aa44,color:#fff
```

**Key enforcement rules:**
- A "pass" verdict without `evidence` (actual command output) on functional criteria is automatically overridden to "fail" by the orchestrator
- Review failure blocks execution — the pipeline halts, not continues
- Unit tests passing alone is NOT sufficient — the contract criterion's verification command must be executed
- The reviewer subprocess runs commands and records `{command, exit_code, stdout_snippet, stderr_snippet}` per criterion

## Data Model

```mermaid
classDiagram
    class AnalysisResult {
        +RepoAnalysis repo
        +SpecAnalysis spec
        +RuntimeAnalysis runtime
        +str route
    }

    class Route {
        +RouteType route_type
        +str reason
        +List~RouteStep~ steps
        +int estimated_tasks
        +bool oracle_needed
    }

    class Plan {
        +List~Phase~ phases
        +str estimated_complexity
        +List~str~ risks
        +List~str~ assumptions
    }

    class Phase {
        +str id
        +str name
        +List~Task~ tasks
    }

    class Task {
        +str id
        +str name
        +str description
        +List~str~ files_to_create
        +List~str~ files_to_modify
        +List~str~ depends_on
        +str model
    }

    class TaskResult {
        +str task_id
        +bool success
        +str commit_hash
        +str summary
        +List~dict~ deviations
        +int attempts
    }

    class Contract {
        +str phase_id
        +str objective
        +List~AcceptanceCriterion~ criteria
        +List~str~ quality_gates
    }

    class Review {
        +str phase_id
        +Verdict verdict
        +List~CriterionResult~ criteria_results
        +List~Finding~ findings
    }

    class TestHarness {
        +str base_url
        +int port
        +AuthConfig auth
        +SeedData seed
        +List~HealthCheck~ health_checks
        +int testability_score
    }

    AnalysisResult --> Route : feeds
    Route --> Plan : determines shape of
    Plan *-- Phase
    Phase *-- Task
    Task --> TaskResult : produces
    Phase --> Contract : verified by
    Contract --> Review : evaluated into
    Plan --> TestHarness : uses for verification
```

## State & Artifacts

All orchestration state lives in `.dirigent/`:

```
.dirigent/
├── ANALYSIS.json          # Repo + spec analysis
├── ROUTE.json             # Selected route + steps
├── PLAN.json              # Execution plan (phases → tasks)
├── STATE.json             # Progress tracking (resumable)
├── DECISIONS.json         # Oracle decision cache
├── SPEC.md                # Copy of input spec
├── test-harness.json      # Endpoint/auth/seed config
├── BUSINESS_RULES.md      # Extracted rules (Legacy route)
├── CONTEXT.md             # Relevant files (Hybrid route)
├── entropy-report.json    # Entropy minimization results
├── summaries/             # Per-task execution summaries
│   └── {task_id}-SUMMARY.md
├── contracts/             # Phase acceptance criteria
│   └── phase-{id}.json
├── reviews/               # Phase review verdicts
│   └── phase-{id}.json
└── logs/                  # Structured execution logs
    ├── run-*.log
    └── run-*.jsonl
```

## Resume & Recovery

```mermaid
stateDiagram-v2
    [*] --> Analyze
    Analyze --> Route
    Route --> Init
    Init --> Planning
    Planning --> Execution

    state Execution {
        [*] --> Task_N
        Task_N --> Task_N: retry (max 3)
        Task_N --> Task_N_Plus_1: success
        Task_N --> Failed: max retries
        Task_N_Plus_1 --> [*]: all done
    }

    Execution --> Test
    Test --> Ship
    Ship --> [*]

    note right of Execution
        STATE.json tracks completed_steps
        and completed_tasks.
        --resume flag skips finished work.
    end note
```

## External Dependencies

| Dependency | Purpose | Required |
|---|---|---|
| **Claude Code CLI** | Task execution engine (subprocess per task) | Yes |
| **Anthropic API** | Oracle architecture decisions | Yes |
| **Git** | Commits, branches, state | Yes |
| **GitHub CLI (gh)** | PR creation | Optional |
| **Outbid Portal** | Real-time event reporting + interactive questions | Optional |
| **Proteus** | Deep domain extraction (5-phase) | Optional |
| **Docker** | Service orchestration for tests | Optional |

## Plugin Skills (19 skills, 18 commands)

The Claude Code plugin (`plugin/.claude-plugin/`) provides skills invoked during execution:

| Skill | Caller | Purpose |
|---|---|---|
| `/dirigent:create-plan` | Planner | Generate PLAN.json from spec + repo context |
| `/dirigent:create-contract` | Contract system | Define phase acceptance criteria |
| `/dirigent:review-phase` | Contract system | Evaluate phase against contract |
| `/dirigent:fix-review` | Contract system | Fix review findings |
| `/dirigent:extract-business-rules` | Executor (Legacy) | Extract business rules from codebase |
| `/dirigent:quick-scan` | Executor (Hybrid/Tracking) | Scan relevant files for context |
| `/dirigent:run-init` | InitPhase | Bootstrap environment + test harness |
| `/dirigent:execute-task` | TaskRunner | Behavioral rules for task execution |
| `/dirigent:increase-testability` | Testability route | Improve test coverage score |
| `/dirigent:add-posthog` | Tracking route | Add PostHog analytics events |
| `/dirigent:build-manifest` | Testability route | Generate outbid-test-manifest.yaml |
| `/dirigent:validate-manifest` | Testability route | Validate manifest against schema |
| `/dirigent:show-plan` | User (CLI) | Render plan for user |
| `/dirigent:show-progress` | User (CLI) | Render execution progress |
| `/dirigent:find-edits` | Research | Find file changes from sessions |
| `/dirigent:find-errors` | Recovery | Surface errors from sessions |
| `/dirigent:search-memories` | Research | Search previous session logs |
| `/dirigent:query-data` | Research | Run DuckDB queries on data files |
| `/dirigent:entropy-minimization` | Executor (all routes) | Align docs, remove dead code, resolve contradictions |

## Key Design Decisions

1. **Subprocess isolation** — Each task runs in a fresh Claude Code process to prevent context window pollution and enable clean retries.

2. **Route-based orchestration** — Analysis-driven route selection adapts the pipeline to the nature of the work (new feature vs. migration vs. test improvement).

3. **Oracle pattern** — Architecture questions are answered via Claude API and cached, enabling fully headless operation without human input.

4. **Evidence-based verification** — Acceptance criteria are defined before execution with executable verification commands. The reviewer must run each command and record output as evidence. The orchestrator rejects "pass" verdicts that lack evidence, and review failure halts the pipeline. Unit tests alone cannot satisfy a criterion — e2e proof is required.

5. **Resumable state machine** — STATE.json tracks every completed step and task, allowing recovery from crashes, timeouts, or network failures.
