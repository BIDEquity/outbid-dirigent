---
name: test-generate
description: Generate unit and functional tests from a /test-review analysis, run them, and auto-fix until green
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, mcp__lbx-ai-backend__codebase-search
---

## Argument parsing

The user may invoke this skill as `/test-generate [taskID] [--file=TestClassName]`.

- `taskID` is an optional ClickUp task ID matching the pattern `DV-\d+` (case-insensitive).
- `--file=TestClassName` is an optional filter to generate only one specific test file from the review
  (match against the test class name, e.g. `--file=DynamicPagePricingConfigurationTest`).

### Determine the task ID

Follow the shared **ClickUp task resolution** convention from CLAUDE.md (all 3 steps — including asking the user if needed).

---

## Step 1: Obtain the test review

### 1a. Locate existing review file

1. Resolve the task ID from argument or branch name.
2. Glob for `.claude-reviews/{taskID}/*_tests.md` (exclude files matching `*_tests_generated*`).
3. If multiple files exist, use the most recent one (by filename timestamp).

### 1b. Staleness check

Run these two commands:
- `stat -c %Y {review_file}` — file modification time
- `git log -1 --format=%ct HEAD` — latest commit time

If the latest commit is **newer** than the review file, the review is **stale**.

### 1c. Decision

| Condition | Action |
|-----------|--------|
| **Fresh review file exists** | Read it. Inform user: "Using existing review from {date}" |
| **No review file found** | Run `Skill(skill: "test-review")`, then glob again and read the generated file |
| **Stale review file** | Inform user: "Review is stale (commits since review). Re-running /test-review..." Then run `Skill(skill: "test-review")` and read the new file |

### 1d. Parse the review

Extract from the "Recommended tests" sections:
- **Test file path** (e.g. `tests/Unit/Domain/.../FooTest.php`)
- **Source file path** (from `**Source:**` line)
- **Setup notes** (from `**Setup:**` line)
- **Test cases table** — each row: test case name, method, code path, lines, ACs
- **Priority** from the "Quick overview" table (P1/P2/P3)
- **Test patterns** from the "Test patterns in this domain" section

If `--file=` was specified, filter to only the matching test file block.

---

## Step 2: Generate tests (P1 → P2 → P3)

Process recommended test files in priority order (P1 first, then P2, then P3).

For each recommended test file:

### 2a. Filter trivially deterministic test cases

Before generating, read the source file and **skip test cases** from the review that test:
- Methods that always return a hardcoded value (`return true`, `return 'constant'`, `return self::KEY`)
- Pure getter/setter methods with no logic
- `getSubscribedEvents()` and similar static wiring methods

Inform the user which cases were skipped and why (e.g. "Skipped `testIsActiveReturnsTrue` — trivially deterministic (`return true`)").

If ALL test cases for a file are skipped, skip the entire file.

### 2b. Read context

1. **Read the source file** referenced in the review (`**Source:**` path).
2. **Read best-practice docs** for mocking and test structure conventions:
   - `tests/Unit/_Doc/mocking_guidlines.md` — Stub vs Mock rules, entity doubles, anti-patterns
   - `tests/Unit/_Doc/codeception_unit_readme.md` — AAA, data providers, vfsStream, real-life examples
3. **Read pattern files** listed in "Test patterns in this domain" section (up to 2 files, first 150 lines each).
4. **Search for existing tests in the same domain** using `Glob` for `tests/Unit/Domain/{Domain}/**/*Test.php` — read one representative file for stub/style conventions.
5. Use `mcp__lbx-ai-backend__codebase-search` if you need to find specific classes, interfaces, or methods referenced in the source.

### 2c. Write the test file

Create the test file following ALL conventions from `.claude/rules/automated_tests.md`:

**Mandatory conventions:**
- Test class extends `Codeception\Test\Unit`
- Use `_before()` for test setup (NOT `setUp()`)
- Use `self::assert...` (NOT `$this->assert...`)
- Use `#[DataProvider('providerName')]` with `use Codeception\Attribute\DataProvider;`
- Data providers: `public static function providerName(): iterable { yield 'label' => [...]; }`
- Service variable named after class (e.g. `$dynamicPagePricingTooltipService`, NOT `$service`)
- Namespace: `LMAP\Tests\Unit\Domain\{Domain}\...` matching the test file path
- AAA structure: Arrange-Act-Assert with clear separation
- Keep tests focused — one assertion concept per test method
- Concrete input/output values derived from reading source code (NOT placeholder values)

**Stubs over mocks:**
- Use `Stub::makeEmpty(Class::class, ['method' => $returnValue])` as the default for test doubles
- Only use `$this->createMock()` when you need `expects($this->once())` or similar interaction verification
- For stubs with constructor: `Stub::construct(Class::class, [$arg], ['method' => $value])`
- Property type for mocks (`createMock()`): use intersection type `OriginalClass&MockObject` (see `.claude/rules/automated_tests.md` "Mock property type hints")
- Property type for stubs (`Stub::makeEmpty()`): just the class/interface type (no intersection needed)

**Assertion resilience:**
- Assert only what the test is about — don't over-constrain
- For collection membership: use `assertContains($expected, $actual)` — NOT `assertCount` + index access
- Assert exact count or order ONLY when count/order is the business requirement under test
- Prefer `assertContains`, `assertArrayHasKey`, `assertStringContainsString` over exact-match when the exact shape is not the point

**Inline comments:**
- For complex test setups or non-obvious arrangements, add short English inline comments
  that explain the *why*, not the *what*. Keep them concise (one line).
- Examples of when to comment:
  - Non-obvious stub return values: `// returns null to simulate missing config`
  - Complex mock chains: `// first call returns draft, second call returns published`
  - Tricky arrange steps: `// entity must be in "approved" state before transition`
  - Assertions on magic values: `// 3 = base price (1) + surcharge (2)`
- Do NOT comment trivial lines like `$result = $service->calculate()` or simple assertions.

**Content requirements:**
- Implement ALL test cases from the review table for this file (after filtering, see below)
- Include all necessary `use` imports (including `use Codeception\Stub;`)
- Create proper stub setup in `_before()` for shared test doubles
- For data providers, yield entries with descriptive labels
- Add type hints for all properties and parameters

### 2d. Write functional test files (Cest classes)

When the test review recommends a **Functional** test, generate a Cest class instead of a Unit
test class. Functional tests use a different structure and conventions:

**Mandatory conventions for Functional tests:**
- Test class is a Cest (NOT extends Unit) — plain class, no parent
- Namespace: `LMAP\Tests\Functional\Domain\{Domain}\...` matching the test file path
- Method signature: `public function testName(CommonStep $I): void`
- Import `use LMAP\Tests\Support\Step\Functional\Common\CommonStep;`
- Grab services from container: `$I->getSymfonyContainer()->get(ServiceClass::class)`
- Use Foundry factories for entity creation: `FieldFactory::createOne([...])`, `UserFactory::createOne([...])`
- Foundry `createOne()` returns a proxy that acts as the entity — do NOT call `->object()` or `->_real()`
- To set entity properties not supported by factory `defaults()`, call setters directly on the
  proxy after creation, or pass custom attributes via `create(['fieldTypeOptions' => [...]])`
- Assertions via `$I->assertSame(...)`, `$I->assertArrayHasKey(...)`, etc.
- AAA structure still applies: clear Arrange / Act / Assert separation

**When to use Functional over Unit:**
- The test verifies that **real DI wiring** produces correct results (not just mocked behavior)
- The test verifies that **Twig rendering** with dynamic context keys resolves correctly end-to-end
- The test verifies that **Doctrine queries** return expected results with real persisted data
- The test guards against **string key mismatches** between components (e.g. context keys, config
  keys) that mocked unit tests cannot catch

**Pattern reference:** Before writing, search for existing Cest files in the same domain:
`tests/Functional/Domain/{Domain}/**/*Cest.php` — read one for factory usage and assertion patterns.

---

## Step 3: Run and auto-fix (per file)

After writing each test file, run and fix it:

### 3a. Run the test

For **Unit** tests:
```bash
TENANT=dummy /app/vendor/bin/codecept run Unit {test_file_path}
```

For **Functional** tests:
```bash
TENANT=dummy /app/vendor/bin/codecept run Functional {test_file_path}
```

### 3b. Evaluate result

| Result | Action |
|--------|--------|
| **All green** | Done. Move to next file. |
| **Test failure — test code issue** | Fix with `Edit` tool, re-run. Issues: wrong mock setup, missing import, incorrect assertion, wrong method signature, missing return type. |
| **Test failure — source code bug** | Do NOT fix source code. Record the issue for the summary report. |
| **Error: class not found / container issue** | Clear cache once: `rm -rf /app/var/tenants/dummy/cache/test` and retry. |

### 3c. Fix loop

- Maximum **3 fix attempts** per test file.
- Each attempt: read error output, identify the root cause, apply targeted `Edit` fix, re-run.
- After 3 failed attempts: stop fixing this file, record remaining errors for the summary.
- Common fixes:
  - Missing `use` import → add it
  - Wrong stub method name → check source and correct
  - Wrong return value in stub array → adjust the value
  - Missing method in stub → add to `Stub::makeEmpty()` array
  - Need interaction verification → switch from `Stub::makeEmpty()` to `createMock()` with `expects()`
  - Missing `&MockObject` intersection type on mock properties → add it (see automated_tests.md)
  - Deprecation notices → ignore (as per project rules)

### 3d. PHPStan validation

After a test file passes (all green), run PHPStan on the generated test file using the
project's test-specific configuration:

```bash
source /app/bin/scripts.sh && phpstan-tests {test_file_path}
```

**Important:**
- Always use `phpstan-tests` (which uses `phpstan_tests.neon`), NOT raw `vendor/bin/phpstan analyse`.
- Pass the specific test file path to only check the generated file, not the entire test suite.

| Result | Action |
|--------|--------|
| **No errors** | Done. Move to next file. |
| **PHPStan errors** | Fix with `Edit` tool, re-run both `codecept` and `phpstan-tests`. Max **2 fix attempts**. |

Common PHPStan issues in generated tests:
- Missing `&MockObject` intersection type on properties using `createMock()`
- Calling `->method()` / `->expects()` on a property typed without `MockObject`
- Wrong parameter types in stub arrays
- Missing `use` imports for PHPUnit types (`PHPUnit\Framework\MockObject\MockObject`)

### 3e. Source bug detection

A failure is likely a **source code bug** (not a test issue) when:
- The test logic matches the review specification exactly
- The mock setup is correct and complete
- The assertion tests documented behavior but the source returns unexpected values
- You have already attempted fixing the test and the failure persists with correct test code

In this case: do NOT modify the source file. Record it as a possible source issue.

---

## Step 4: Summary output

After all test files are processed, output a summary:

```markdown
## Test Generation Summary

**Task:** {taskID} — {task title} | **Generated:** {N} files | **Tests:** {M} total

| Test file | Cases | Status | Notes |
|-----------|-------|--------|-------|
| DynamicPagePricingConfigurationTest | 13 | ✅ Green | — |
| DynamicPagePricingTooltipServiceTest | 12 | ✅ Green | — |
| SomeOtherTest | 8 | ⚠️ 2 failing | Possible source bug (see below) |
| AnotherTest | 5 | ❌ 3 errors | Max fix attempts reached |
```

If there are possible source issues, add:

```markdown
### Possible source issues
- `SomeService.php:45` — returns null when config is missing, but documented behavior expects default value
  (detected by `testGetValueReturnsDefaultWhenConfigMissing`)
```

If there were errors that could not be fixed:

```markdown
### Remaining test errors
- `AnotherTest::testSomeCase` — `Call to undefined method Foo::bar()` (method may have been renamed)
```

---

## Key conventions

- **Tenant**: Set `TENANT=dummy` as env prefix for `codecept`
- **Test command (Unit)**: `TENANT=dummy /app/vendor/bin/codecept run Unit {path}`
- **Test command (Functional)**: `TENANT=dummy /app/vendor/bin/codecept run Functional {path}`
- **Cache clear**: `rm -rf /app/var/tenants/dummy/cache/test` (only once, on container/cache errors)
- **Never fix source code** — only fix test code. Report source issues to the user.
- **Follow all rules** from `.claude/rules/automated_tests.md` and `.claude/rules/test_coverage_review.md`
- **Read before writing** — always read the source file and pattern files before generating a test
- **Concrete values** — derive test input/output values from reading the actual source code, never use placeholder data
