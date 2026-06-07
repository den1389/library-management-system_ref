# Testing Strategy for AI Assistants

## Framework
- pytest + pytest-cov
- Target: 200+ tests, >70% coverage, 0 bugs/vulnerabilities

## Test Structure
```
tests/
├── conftest.py              # Shared fixtures (book_repo, user_repo, service, etc.)
├── unit/
│   ├── test_book_model.py   # Model-level unit tests
│   ├── test_user_model.py
│   ├── test_loan_model.py
│   ├── test_fine_strategy.py
│   ├── test_repositories.py
│   └── test_observer.py
└── integration/
    ├── test_borrow_return.py
    ├── test_reservations_users_fines.py
    └── test_edge_cases.py
```

## Running Tests
```bash
# All tests with coverage
pytest --cov=src --cov-report=html:coverage_html --cov-report=xml:coverage.xml --junitxml=junit.xml -v

# Quick run
pytest -v

# Specific file
pytest tests/unit/test_fine_strategy.py -v

# With coverage threshold enforcement
pytest --cov=src --cov-fail-under=70
```

## Reports Generated
| Report | Path | Purpose |
|--------|------|---------|
| JUnit XML | junit.xml | SonarQube integration |
| Coverage XML | coverage.xml | SonarQube coverage |
| HTML Coverage | coverage_html/ | Visual inspection |

## Test Naming Convention
- `test_<action>_<condition>_<expected_result>`
- Example: `test_borrow_blocked_user_raises_error`

## Fixture Usage (from conftest.py)
```python
def test_example(service, notification_repo):
    user = service.register_user("Name", "email@test.com")
    book = service.add_book("Title", "Author", "ISBN", 2020, "Genre")
    loan = service.borrow_book(user.id, book.id)
    assert loan is not None
```

## Coverage Rules
- Every public method in src/services/ must be covered
- Every branch in business logic (if/else) must have a test
- Edge cases: empty collections, zero values, boundary values, None inputs
- Error cases: each custom exception must be triggered by at least one test

## Mock Usage
- Mock ONLY external dependencies (none in this project — all in-memory)
- Use MagicMock for EventObserver in observer tests
- NEVER mock the service itself in integration tests
