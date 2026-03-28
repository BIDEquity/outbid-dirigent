---
name: extract-business-rules
description: Extract all business rules from a legacy codebase
---

# Extract Business Rules

Systematically analyze the codebase and extract all business rules.

## Output

Create `.dirigent/BUSINESS_RULES.md`:

```markdown
# Business Rules — {PROJECT_NAME}

## Core Entities
(All domain objects and their fields)

## Business Rules
(Validations, calculations, constraints)

## Domain Events
(What happens when? User creates X → Y is triggered)

## API Endpoints
(All routes with parameters and response format)

## Database
(Schema, relations, constraints)

## External Dependencies
(APIs, services, integrations)

## Edge Cases
(Known special cases and how they're handled)
```

## Rules

1. Be precise. No assumptions. Only what you see in code.
2. Document numeric values exactly (limits, timeouts, etc.)
3. Mark uncertainty with [UNCLEAR]
4. Analyze all relevant files systematically
5. Don't miss validation rules, constraints, or business logic
