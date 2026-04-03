# Testing Strategy

## Framework
- **pytest** for all tests
- Tests in `tests/` directory

## Approach
- Unit tests only (no services, no infrastructure)
- Each module gets its own test file: `tests/test_{module}.py`
- Test happy path + edge cases (empty string, zero, negative)

## Running Tests
```bash
python -m pytest tests/ -v
```
