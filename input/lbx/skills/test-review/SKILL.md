---
name: test-review
description: Review test coverage of the current changeset against ClickUp acceptance criteria
context: fork
agent: general-purpose
allowed-tools: Bash(git *), Read, Glob, Grep, mcp__clickup__get_task, mcp__clickup__get_task_comments, mcp__lbx-ai-backend__codebase-search
disable-model-invocation: true

---

## Argument parsing

The user may invoke this skill as `/test-review [taskID]`.

- `taskID` is an optional ClickUp task ID matching the pattern `DV-\d+` (case-insensitive).

### Determine the task ID

Follow the shared **ClickUp task resolution** convention from CLAUDE.md (all 3 steps — including asking the user if needed).

---

## Step 0: Check for prior task-review

Before analyzing test coverage, check whether a code review (`/task-review`) has already been
performed for this task.

### 0a. Look for an existing task-review file

Search for `.claude-reviews/{taskID}/*.md` files that are **not** test-review files
(test-review files contain `-tests-` in their name).

- Use `Glob` with pattern `.claude-reviews/{taskID}/*.md` (excluding `*-tests-*`).

### 0b. No task-review found

If no prior task-review file exists, ask the user using `AskUserQuestion`:

> No code review (`/task-review`) was found for this task. A code review can identify
> architectural issues, bugs, or design problems that should be resolved before writing tests.
>
> How would you like to proceed?
> 1. Run `/task-review` first, then come back to `/test-review`
> 2. Continue with `/test-review` without a prior code review

If the user selects option 1, inform them to run `/task-review` first and stop execution.

### 0c. Task-review exists with high severity findings

If a task-review file is found, read it and check for **High** severity findings.
If high severity findings exist, ask the user using `AskUserQuestion`:

> A prior code review was found with **high severity** findings:
> {list the high severity finding titles briefly}
>
> Writing tests for code that may need significant changes could result in wasted effort.
> How would you like to proceed?
> 1. Stop — resolve the high severity issues first, then run `/test-review`
> 2. Continue with `/test-review` anyway (tests may need to be rewritten after fixes)

If the user selects option 1, stop execution.

### 0d. Task-review exists without high severity findings

Proceed directly to Step 1. No user interaction needed.

---

## Step 1: Gather context

### 1a. ClickUp task

When a task ID is resolved:
1. Fetch the task using `mcp__clickup__get_task`.
2. Fetch comments using `mcp__clickup__get_task_comments`.
3. Extract all **acceptance criteria (ACs)** from the task description and comments.
4. If ClickUp is unreachable, inform the user and continue without AC context.

### 1b. Branch changeset

Collect the full changeset on the current branch:
- Committed changes: !`git diff main...HEAD`
- Staged changes: !`git diff --cached`
- Changed file list: !`git diff main...HEAD --name-only`
- Commit log: !`git log main..HEAD --format="commit %H%n    %s%n"`

### 1c. Existing tests and patterns

For every changed source file, check whether a corresponding test already exists:
- For `src/Domain/{Domain}/{Type}/{ClassName}.php` → search for `tests/Unit/Domain/{Domain}/**/{ClassName}Test.php`
- For controllers → search for `tests/Functional/Domain/{Domain}/**/*Cest.php`
- Use `Glob` to find matches. Also use `mcp__lbx-ai-backend__codebase-search` to find related test classes.

Additionally, identify **existing test files in the same domain** that can serve as patterns:
- Search for `tests/Unit/Domain/{Domain}/**/*Test.php` and `tests/Functional/Domain/{Domain}/**/*Cest.php`
- Note which mock patterns, factory usage, or helper methods they use
- These will be referenced in the output as implementation examples for the developer

---

## Step 2: Analyze each changed file

For every changed/added PHP file in the changeset, determine:

1. **What kind of code is it?** (Service, Entity, Controller, MessageHandler, Repository, Validator, Twig, DTO, Config, etc.)
2. **Does it contain testable logic?** Apply the boundaries from `.claude/rules/test_coverage_review.md`:
   - Business logic with branching/transformation → testable
   - Pure DTO/getter/setter/config → skip
3. **Is it testable in its current form?** Check for god-functions, dependency overload, static coupling (thresholds from the rule file).
4. **Which test type is appropriate?** Use the "Test type decision guide" from the rule file.
   **Always check for the "Both unit AND functional" case.** A service that contains isolated
   business logic (branching, transformation) AND also integrates with infrastructure services
   (Twig rendering, Doctrine queries, DI wiring, cache) in a way that matters for correctness
   should get BOTH a unit test (for isolated logic paths) AND a functional test (for the real
   integration). Common signals:
   - The service calls Twig/template rendering with dynamic context keys
   - The service queries Doctrine with custom QueryBuilder logic
   - The service chains multiple injected services where the wiring itself is load-bearing
   - Hardcoded string keys (e.g. array keys, Twig context names) couple the service to other
     components — a functional test catches key mismatches that mocked unit tests cannot.
   When recommending "Both", include separate entries in the Quick Overview table (one Unit, one
   Functional), and explain in each test block what specifically it covers that the other cannot.
5. **Does a test already exist?** If yes, does it adequately cover the changed logic?
6. **Apply exclusions** from `.claude/rules/test_coverage_review.md` "What does NOT need dedicated
   tests" section. In particular, do NOT recommend tests for:
   - `getSubscribedEvents()`, `getSubscribedServices()`, and similar static wiring methods
   - Trivially deterministic methods (hardcoded return values)
   - Pure delegation methods (forwarding to another service with no logic)
7. **Can it be mapped to an AC?** If the file contains testable logic but does NOT map to any AC
   (e.g. helper classes, utility methods, internal refactors, new abstractions), mark it as
   **non-AC code**. These still need test recommendations — they are treated equally in the
   "Recommended tests" section, but their ACs column shows "—" and they are counted separately
   in the verdict.

---

## Step 3: Output the review

**Layout principles:**
- **Verdict first** — one-liner banner. The developer knows in 1 second if action is needed.
- **Quick overview** — compact table after the verdict showing all recommended test files
  with priority (P1 = core business logic, P2 = service layer, P3 = subscribers/integration),
  number of test cases, and complexity (Low/Medium/High based on mock count and setup effort).
  This helps the developer know where to start and helps Claude prioritize test generation.
- **AC table** — single unified table with AC description, coverage status, and which test covers
  it (or "—" if out of scope). This is the ONLY place ACs appear. No separate "extracted ACs"
  list, no separate "AC mapping" table.
- **Recommended tests** — per target test file, one flat table. Each row = one test case.
  The ACs column on each test row cross-references back to the AC table above.
- **No repetition** — each fact appears exactly once.

**Priority assignment rules:**
- **P1**: Pure domain models, value objects, static utility classes — core logic, easy to test
- **P2**: Services with injectable dependencies — business logic requiring mocks
- **P3**: Subscribers, event listeners, controllers — integration-heavy, complex mock setup

Structure the output as follows:

```markdown
## Test Coverage Review

> ✅ **Top coverage!** All ACs are covered by tests. {optional: short note}

OR

> ⚠️ **Needs work** — {X} of {Y} ACs lack test coverage{optional: + N non-AC methods untested}. See recommendations below.

OR

> 🚫 **Blocked** — {N} testability issues must be resolved before tests can be written.

**Task:** {taskID} — {task title} | **Branch:** {branch name} | **Files:** {count}

**Quick overview:**
| Priority | Test file | Cases | Complexity |
|----------|-----------|-------|------------|
| P1 | DynamicPagePricingConfigurationTest | 13 | Low (value object, no mocks) |
| P1 | DynamicPagePricingConfigurationMapperTest | 6 | Medium (mock EntityManager) |
| P2 | ... | ... | ... |

### Acceptance criteria

| # | AC | Can be covered by (see below) | Status |
|---|----|-------------------------------|--------|
| 1 | Campaign column added to Order Evaluation | `testAddsHeaderForSupportedType` | ⚠️ Gap |
| 2 | Only when campaign addon active | `testSkipsWhenInactive`, `testRowSkipsWhenInactive` | ⚠️ Gap |
| 3 | Display campaign title and ID | `testOutputsCampaignTitleAndId` | ⚠️ Gap |
| 4 | Format: title (id) | `testOutputsCampaignTitleAndId` | ⚠️ Gap |
| 5 | Empty when no campaign | `testOutputsEmptyCell` (2 variants) | ⚠️ Gap |
| 6 | Correct campaign per item | `testOutputsCampaignTitleAndId` | ⚠️ Gap |
| 7 | Column always present when active | `testAddsHeaderForSupportedType` | ⚠️ Gap |
| 8 | Only booked items listed | — (query-level, not in changeset) | — |
| 9 | Extended to Social Media | DataProvider tests for all 3 types | ⚠️ Gap |

Status values: ✅ = test exists and covers the AC, ⚠️ Gap = test recommended but missing, — = out of scope

### Testability issues

Only if there are blockers. Omit entirely if none.

| File:line | Method | Issue | Recommendation |
|-----------|--------|-------|----------------|
| `FooService.php:45` | `processAll()` | 58 lines, 3 responsibilities | Split into `validate()`, `mapToDto()`, `persist()` |

### Recommended tests

#### `tests/Unit/Domain/{Domain}/.../SomeListenerTest.php` (new)

**Source:** `src/Domain/.../SomeListener.php`
**Setup:** Mock `TranslatorInterface`, mock `ConfigurationEntityService`. Create real event objects.

| Test case | Method | Code path | Lines | ACs |
|-----------|--------|-----------|-------|-----|
| `testAddsHeaderForSupportedType` | `reportingHeaders()` | Happy path: adds translated header | 43-58 | #1, #7 |
| `testSkipsHeaderForUnsupportedType` | `reportingHeaders()` | Guard: unsupported type → early return | 35-37 | #2 |
| `testSkipsHeaderWhenInactive` | `reportingHeaders()` | Guard: inactive → early return | 39-41 | #2 |
| `testOutputsCampaignTitleAndId` | `reportingRow()` | Campaign exists → "Title (ID)" | 70-75 | #3, #4, #6 |
| `testOutputsEmptyCellWhenNoCampaignAction` | `reportingRow()` | No campaign action → empty cell | 77-80 | #5 |
| `testOutputsEmptyCellWhenCampaignIsNull` | `reportingRow()` | Campaign action exists but campaign null | 77-80 | #5 |
| `testSkipsRowForNonOrderItem` | `reportingRow()` | Guard: wrong entity type | 62-64 | — |
| `testWorksForAllSupportedTypes` | `reportingRow()` | DataProvider: 3 report types | 60-82 | #9 |

### Not requiring tests
- `SocialMediaReportingType.php` — cosmetic refactor, no logic change
- Translation files (14) — static YAML config

### Existing coverage ✅
- `FooServiceTest` covers `calculate()` — adequate

### Test patterns in this domain
- `tests/Unit/Domain/ArticlePricingConfiguration/ArticlePricingMappingServiceTest.php` —
  Mock setup for `ArticlePricingConfiguration` + `EntityManager`, data provider usage
- `tests/Unit/Domain/Order/Entity/OrderItemTest.php` —
  OrderItem entity test patterns
```

### Output rules
- The blockquote verdict banner is ALWAYS the first element after the heading.
- **AC table appears exactly once.** It combines: AC description + which test covers it + status.
  Do NOT output a separate "extracted ACs" list or a separate "AC mapping" table. This single
  table IS the AC list AND the coverage mapping.
- The "Can be covered by (see below)" column references the recommended test case names from
  the "Recommended tests" section. For ACs already covered by existing tests, change the column
  header to "Covered by" and the status to ✅. For out-of-scope ACs, use "—".
- Group all recommended test cases per target test file into ONE table.
- The "ACs" column on each test case row cross-references the AC numbers from the table above.
- The "Setup" note appears once per test file block.
- **NEVER place a `---` (horizontal rule) directly after a markdown table.** Many renderers
  (including ClickUp comments, GitHub, and terminal markdown viewers) will misinterpret the
  `---` as a table header separator, breaking the table rendering. Instead, use `### Heading`
  elements to separate sections — they provide sufficient visual separation on their own.
  If you must use `---`, ensure there is at least one non-empty, non-table line (e.g. a text
  paragraph) between the table and the `---`.
- Omit any section that has no entries.
- Always include **file path with line numbers**.
- The "Quick overview" table appears directly after the Task/Branch/Files line, before the AC table.
  It lists every recommended test file with priority (P1/P2/P3), number of test cases, and
  complexity (Low/Medium/High). Omit if there are no recommended tests.
- The "Test patterns" section lists 1-3 existing test files from the same or related domain
  that serve as implementation reference. Each entry describes what pattern it demonstrates
  (mock setup, factory usage, data providers, etc.). Omit if no relevant patterns exist.

### Verdict criteria for the banner
- **✅ Top coverage!** — All ACs have adequate test coverage AND no untested non-AC logic, no testability blockers.
- **⚠️ Needs work** — One or more ACs lack test coverage, OR there is untested non-AC logic (helpers, utilities, internal methods with branching), or there are non-blocking gaps.
- **🚫 Blocked** — Testability blockers exist that must be resolved first.

Note: Non-AC code (helpers, mappers, utility methods) that contains testable logic counts toward
the verdict. A changeset where all ACs are covered but a complex helper method is untested is
still "Needs work".

---

## Step 5: Save and offer to post

If a task ID was resolved:
1. `mkdir -p .claude-reviews/{taskID}`
2. Save the review to `.claude-reviews/{taskID}/{Ymd-Hi}_tests.md`
3. `git add {review file}` (no commit)
4. Output the results to the user.
5. Ask the user using `AskUserQuestion` whether they want to post the review as a comment on the ClickUp task.
6. If yes, post via `mcp__clickup__add_task_comment`.

If no task ID was resolved:
1. Output the results to the user directly.
