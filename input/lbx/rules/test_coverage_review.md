## Test Coverage Review

When reviewing code changes (MR review or changeset review), always evaluate test coverage
using the boundaries and test type recommendations defined below.

---

### Test type decision guide

This project uses three test suites. For every piece of changed/added logic, recommend the
appropriate test type based on what is actually being exercised:

#### Unit tests (`tests/Unit/`)
Recommend a **unit test** when the code under review:
- Contains **pure business logic** — calculations, transformations, branching, validation rules
- Is a **service method** that can be isolated by mocking its dependencies
- Is an **entity method with logic** — state transitions, computed values, conditional behavior
- Is a **value object** with validation, normalization, or comparison
- Is a **validator / constraint validator** with conditional rules
- Is a **utility / helper** with static or stateless methods
- Is a **MessageHandler** where the `handle()` logic can be tested by mocking repositories and
  other services (happy path + error/edge cases)
- Benefits from **data providers** to cover multiple input/output variations efficiently

Unit tests use `Codeception\Test\Unit`, mock dependencies via `createMock()` / `Stub::makeEmpty()`,
and must NOT touch the database or Symfony container.

#### Functional tests (`tests/Functional/`)
Recommend a **functional test** when the code under review:
- Is a **controller action** — test the HTTP request/response cycle, status codes, redirects,
  flash messages, and rendered output via `$I->see()` / `$I->seeElement()`
- Involves **Twig template rendering** — test that translated strings, conditional blocks, form
  elements, and dynamic content appear correctly in the HTML output
- Is a **service that orchestrates multiple real dependencies** and the integration between them
  is what matters (e.g. cart calculation with real DB entities, workflow transitions)
- Tests **Doctrine query logic** in repositories — real QueryBuilder with persisted test data
  via Foundry factories
- Tests **DI wiring** — that a service is correctly registered and autowired
- Tests **Symfony Workflow transitions** — real state machine with entity state
- Tests **event dispatch / subscriber integration** — that events are actually dispatched and
  handled in the container

Functional tests use Codeception Cest classes with `FrontofficeStep` / `BackofficeStep` actors,
persist data via Foundry factories (`*Factory::createOne()`), and run inside a DB transaction
(auto-rollback).

#### API tests (`tests/Api/`)
Recommend an **API test** when the code under review:
- Is a **REST API endpoint** (`/api/v1/...`) — test JSON response structure, status codes,
  filtering, serialization output
- Changes **API serialization** or **response format**

API tests use `ApiStep` with the Codeception REST module.

#### Both unit AND functional
Recommend **both** when:
- A service contains complex business logic (→ unit test for isolated logic paths) AND
  integrates with Doctrine/other services in a way that matters (→ functional test for the
  real integration). Example: `AdvertisingSubsidyCartService` has unit tests for price
  summation logic and functional tests for real cart interaction with persisted entities.
- A new feature adds a service + controller route — unit test the service, functional test
  the controller/template.

---

### What MUST be tested

| What | Test type | When |
|------|-----------|------|
| Service with business logic (`Domain/*/Service/`) | Unit | Every public method with branching, transformation, or side effects |
| MessageHandler `handle()` methods | Unit | Happy path + at least one error/edge case |
| Entity methods with logic | Unit | State transitions, computed values, validation (not plain getters/setters) |
| Value Objects with validation/normalization | Unit | Construction rules, comparison, transformation |
| Validator / ConstraintValidator | Unit | Each validation rule path |
| Controller actions (new or changed routes) | Functional | HTTP status, redirects, flash messages, rendered content |
| Twig template changes (conditional blocks, new elements) | Functional | `$I->see()` / `$I->seeElement()` for expected output |
| Repository methods with custom query logic | Functional | Real DB with Foundry-created test data |
| Workflow transitions (new states or guards) | Functional | `$workflow->can()` with real entity state |
| REST API endpoints | API | JSON structure, status codes, filtering |

### What does NOT need dedicated tests

- Pure DTOs and data-transfer classes with no logic
- Trivial getters / setters / property accessors
- Doctrine mapping configuration (column definitions, relation annotations)
- Symfony DI configuration and compiler passes (unless wiring is non-trivial)
- Constants-only classes or Enums without methods
- Private methods — test them indirectly through the public method that calls them
- Configuration / parameter classes
- **Event wiring methods** — `getSubscribedEvents()`, `getSubscribedServices()`, and similar
  framework hook methods that only return a static mapping array. These change frequently as
  features are added, creating high maintenance cost with near-zero value. The wiring is
  implicitly tested by functional tests that trigger the events.
- **Trivially deterministic methods** — methods that always return the same hardcoded value
  (e.g. `isActive()` returning `true`, `getType()` returning a string constant, `getName()`
  returning a class constant). If a method has no branches and no computation, it does not
  need a test.
- **Pure delegation methods** — methods that do nothing but forward to another service with
  no additional logic (e.g. Twig extensions that just call a service method and return the
  result). Test the underlying service instead.

---

### Testability assessment — flag issues before requesting tests

Before asking for tests, check whether the code under review is actually testable in its
current form. Flag the following as **refactoring prerequisites** — do not request tests
for untestable code; request a refactor first.

#### God-function detection

Flag a method when ANY of these apply:

- **Method length > 40 lines of logic** (excluding blank lines, comments, and simple
  assignments/returns). Suggest extracting cohesive blocks into private or separate service methods.
- **Cyclomatic complexity is high** — more than 6-8 independent branches (if/elseif/switch cases/
  ternaries/null-coalescing with fallback logic). Each branch multiplies the number of test cases needed.
- **Multiple responsibilities in one method** — e.g. validation + transformation + persistence +
  notification in a single method. Look for groups of statements that could be described with
  different verbs ("validates", "maps", "persists", "notifies"). Each group should be its own method.
- **Deep nesting > 3 levels** (excluding simple early returns and single-level closures).
  Deeply nested code is hard to test because setup complexity grows exponentially.
- **Method mixes query and command** — it both reads/computes a result AND causes side effects.
  Suggest separating the query part from the command part (CQS principle).

#### Dependency overload

- **Constructor has > 15 dependencies** — this is a strong signal of SRP violation. The class is
  likely doing too much. Suggest splitting into focused services before writing tests.
- Note: 6-12 constructor dependencies is normal in this codebase due to DI wiring and infrastructure
  services (EntityManager, EventDispatcher, Translator, Logger, etc.). Do NOT flag this range.

#### Static / global coupling

- Method relies on static state, global variables, or singletons that cannot be replaced in tests.
  Suggest injecting these as dependencies instead.

---

### Review output format

When performing test coverage review, structure the output as follows:

```
### Test Coverage Review

#### Testability issues (refactor before writing tests)
| File | Method | Issue | Recommendation |
|------|--------|-------|----------------|
| ...  | ...    | God-function (58 lines, 3 responsibilities) | Extract X, Y, Z into separate methods |

#### Coverage gaps
| File | Method | Recommended test type | Reason |
|------|--------|-----------------------|--------|
| FooService.php | handleBar() | Unit | Business logic with 3 branches, no test exists |
| BazController.php | indexAction() | Functional | New route, needs HTTP + template assertion |
| QuxService.php | processOrder() | Unit + Functional | Complex logic (unit) + DB integration (functional) |

#### Existing test coverage ✅
- `FooServiceTest` covers `calculate()` — adequate
- `BazControllerCest` covers `indexAction()` — adequate
```

If there are no gaps or issues in a section, omit that section entirely.
Place "Testability issues" first — these block everything else.

---

### Severity classification

- **Testability blocker** — god-functions or SRP violations that make testing impractical.
  This blocks both the tests AND the implementation — request refactoring first.
- **Must have tests** — new/changed public service methods and handlers with business logic,
  new controller routes, changed Twig output with conditional logic.
  This is a blocking review finding.
- **Should have tests** — edge cases in existing logic that changed, complex private methods
  extracted from public ones, minor template changes.
  This is a non-blocking recommendation.

---

### What counts as adequate test coverage

- Happy path is covered
- At least one error / edge case per branch that has business impact
- Data providers are used when testing the same logic with multiple input variations
- Mocks are used for external dependencies (repositories, external APIs, mailers) — not for
  the unit under test itself
- Functional tests use Foundry factories for data setup, not raw SQL or manual entity construction
- Tests follow AAA structure (Arrange-Act-Assert) as defined in `automated_tests.md`
- For services with both isolated logic and integration concerns: both unit and functional
  tests exist, each covering their respective aspect
