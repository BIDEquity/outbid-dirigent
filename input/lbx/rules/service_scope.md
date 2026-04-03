## Service Scope Documentation

Reference: `src/_Doc/best_practice/service_scope.md`

### When generating or modifying code

- Every service class MUST have a one-to-two-sentence English PHPDoc class comment describing
  its responsibility scope (what it owns, not how it works).
- When creating a new service, always generate this scope comment.
- When adding logic to an existing service, check if the new logic fits the declared scope.
  If it violates the scope: create a new service with its own scope instead of expanding
  the existing one.

### When reviewing code (MR review / changeset review)

Check for the following and flag violations:

| Check | Severity |
|-------|----------|
| New or changed service class has no scope doc comment | **Must fix** — add a scope comment |
| Scope doc comment is too vague (e.g. "Service for articles") | **Must fix** — make it specific |
| New logic in a service clearly falls outside its declared scope | **Must fix** — extract to a new service |
| Scope comment was widened to accommodate unrelated logic | **Must fix** — revert scope, extract logic |

### Example

```php
/**
 * Handles price calculation and discount application for cart line items.
 */
class CartPriceService
{
    // Adding email-sending logic here would violate the scope.
    // → Create a separate OrderNotificationService instead.
}
```
