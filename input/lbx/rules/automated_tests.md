## Automated Testing
- For automated testing we use codeception
- Functional tests are located in `tests/Functional`
- Unit tests are located in `tests/Unit` and extend from `\Codeception\Test\Unit`
- Adhere to "Arrange-Act-Assert" (AAA) structure for clarity when writing your tests.
- Keep your unit tests focused and concise, isolating a single piece of functionality each.
- If there are static functions to test call them directly without mocking
- Use data providers in unit tests by using #[DataProvider('dataProviderName')] , yield entries
- Use `self::assert...`, not `$this::assert...` and not `$this->assert...`
- When creating a new test place it in the same domain under tests and the file under test
- If a test focuses on testing a single service name the service variable with the service's class name, not just 'service'
- To run tests use:
    - `mp-tenant dummy && codecept run Unit {test_file_name}`
    - `mp-tenant dummy && codecept run Functional {test_file_name}`
    - example: `mp-tenant dummy && codecept run Unit tests/Unit/Domain/AdvertisingAssociation/Entity/AdvertisingAssociationTest.php:28`
- Ignore deprecation notices in tests
- If tests fail its likely due to incomplete container dumps because the test environment is executed in non debug mode. Clear the cache directory once here: `/app/var/tenants/dummy/cache/test`
- If all tests should be reexcuted please use the following script wrappers:
  - execute all test types: `mp-test-pipeline-unit && mp-test-pipeline-functional && mp-test-pipeline-api`
  - execute only unit tests: `mp-test-pipeline-unit`
  - execute only functional tests: `mp-test-pipeline-functional`
  - execute only api tests: `mp-test-pipeline-api`

### Unit vs Functional — when to use which

| Code under test | Test type | Why |
|-----------------|-----------|-----|
| Service with business logic, branching, transformation | **Unit** | Isolate with mocks/stubs, fast feedback |
| Entity method with state transitions or computed values | **Unit** | Pure logic, no DB needed |
| Value Object with validation/normalization | **Unit** | Pure logic |
| Validator / ConstraintValidator | **Unit** | Each validation rule path |
| MessageHandler `handle()` | **Unit** | Mock repos and services |
| Controller action (HTTP cycle, redirects, flash messages) | **Functional** | Needs Symfony kernel + request/response |
| Twig template rendering (conditional blocks, translated strings) | **Functional** | Needs real template engine |
| Repository with custom query logic | **Functional** | Needs real DB with test data (Foundry) |
| REST API endpoint (JSON structure, status codes) | **API** | Needs full HTTP stack |
| Complex service with both isolated logic AND DB integration | **Unit + Functional** | Unit for logic paths, Functional for real integration |

For the full decision guide with detailed criteria, see `.claude/rules/test_coverage_review.md`.

### Mock property type hints

When storing a mock as a class property, **always use the intersection type** `OriginalClass&MockObject`:

```php
// Good — IDE and PHPUnit both understand the type
private ConfigurationEntityService&MockObject $configurationEntityService;

// Bad — calling ->method() or ->expects() triggers IDE warnings / static analysis errors
private ConfigurationEntityService $configurationEntityService;
```

**Why:** Without `&MockObject`, the property type only declares the original class. PHPUnit's
`createMock()` returns `MockObject&OriginalClass`, but if the property is typed as just the
original class, calls like `->method()` and `->expects()` are not recognized — leading to
"method not found" warnings in IDEs and static analysis tools.

This applies to all mocks stored as properties. Inline mocks assigned to local variables
typically don't need this because the type is inferred from `createMock()`.

### Stubs vs Mocks

- **Prefer Codeception `Stub::makeEmpty()`** for test doubles that only return values:
  ```php
  // Good — concise, readable
  $orderItem = Stub::makeEmpty(OrderItem::class, [
      'getArticle' => $article,
      'getCurrentQuantity' => 100,
  ]);

  // Avoid — verbose, no added value when you don't verify interactions
  $orderItem = $this->createMock(OrderItem::class);
  $orderItem->method('getArticle')->willReturn($article);
  $orderItem->method('getCurrentQuantity')->willReturn(100);
  ```
- **Use `createMock()` only** when you need interaction verification (`expects($this->once())`, `expects($this->never())`, etc.)
- For stubs with constructor arguments, use `Stub::construct(Class::class, [$arg1], ['method' => $value])`

### Assertion resilience

- **Assert only what the test is about.** Don't over-constrain assertions.
- When testing collection membership, use `assertContains` instead of `assertCount` + index access:
  ```php
  // Good — resilient to additions
  self::assertContains(PageflexCompilationComponent::$componentKey, $keys);

  // Avoid — breaks when a new key is added
  self::assertCount(1, $keys);
  self::assertSame(PageflexCompilationComponent::$componentKey, $keys[0]);
  ```
- Assert exact count or order **only** when the count/order is the business requirement under test.
- Prefer `assertContains`, `assertArrayHasKey`, `assertStringContainsString` over exact-match assertions when the exact shape is not the point of the test.
