# Architecture Rules for AI Assistants

## System Overview
Library Management System with In-Memory storage, built using layered architecture.

## Layer Structure

```
src/
├── models/        # Pure domain entities (no business logic beyond validation)
├── services/      # Business logic, orchestration, patterns
├── storage/       # Repository interfaces + In-Memory implementations
└── utils/         # Pure utility functions
```

## Dependency Direction (STRICT)
```
services → storage/interfaces (abstract)
services → models
storage/in_memory → models
storage/in_memory implements storage/interfaces
```
- Services NEVER import from storage/in_memory directly — only from interfaces
- Models NEVER import from services or storage

## In-Memory Storage Pattern
Every entity uses a Dict[str, Entity] as its backing store:
```python
class InMemoryXRepository(XRepository):
    def __init__(self):
        self._store: Dict[str, X] = {}
```
- No file I/O, no SQLite, no shelve — pure memory only
- Thread safety is NOT required for this project

## GoF Patterns Used

### Strategy (FineStrategy)
- Location: src/services/fine_strategy.py
- Context: FineCalculator
- Strategies: StandardFineStrategy, ProgressiveFineStrategy, FlatFineStrategy, WeeklyFineStrategy
- To add new strategy: create class extending FineStrategy, implement calculate() and name()

### Observer (EventBus + EventObserver)
- Location: src/services/observer.py
- Subject: EventBus (central pub/sub)
- Observer: NotificationObserver (creates Notification entities)
- Events: book_returned, book_overdue, fine_charged, user_blocked, book_available, reservation_ready, loan_extended
- To add new event: publish_event() in service, add handler in NotificationObserver

## SOLID Compliance
- **S**: Each class has one reason to change
- **O**: Add new fine algorithms without modifying FineCalculator
- **L**: All repository implementations can substitute their interface
- **I**: BookRepository/UserRepository/LoanRepository are separate interfaces
- **D**: LibraryService depends on abstract Repository, not InMemory* classes
