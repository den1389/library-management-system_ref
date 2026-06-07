"""In-Memory repository implementations."""
from typing import Dict, List, Optional

from src.models.book import Book, BookStatus
from src.models.loan import Loan, LoanStatus
from src.models.notification import Notification
from src.models.user import User, UserRole, UserStatus
from src.storage.interfaces import (
    BookRepository,
    LoanRepository,
    NotificationRepository,
    UserRepository,
)


class InMemoryBookRepository(BookRepository):
    def __init__(self):
        self._store: Dict[str, Book] = {}

    def save(self, entity: Book) -> Book:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Book]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Book]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def find_by_isbn(self, isbn: str) -> Optional[Book]:
        return next((b for b in self._store.values() if b.isbn == isbn), None)

    def find_by_author(self, author: str) -> List[Book]:
        return [b for b in self._store.values() if author.lower() in b.author.lower()]

    def find_by_genre(self, genre: str) -> List[Book]:
        return [b for b in self._store.values() if b.genre.lower() == genre.lower()]

    def find_available(self) -> List[Book]:
        return [b for b in self._store.values() if b.status == BookStatus.AVAILABLE]

    def search(self, query: str) -> List[Book]:
        q = query.lower()
        return [
            b for b in self._store.values()
            if q in b.title.lower() or q in b.author.lower() or q in b.isbn
        ]

    def count(self) -> int:
        return len(self._store)


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._store: Dict[str, User] = {}

    def save(self, entity: User) -> User:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: str) -> Optional[User]:
        return self._store.get(entity_id)

    def find_all(self) -> List[User]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def find_by_email(self, email: str) -> Optional[User]:
        return next((u for u in self._store.values() if u.email == email), None)

    def find_by_role(self, role: str) -> List[User]:
        return [u for u in self._store.values() if u.role.value == role]

    def find_blocked(self) -> List[User]:
        return [u for u in self._store.values() if u.status == UserStatus.BLOCKED]

    def count(self) -> int:
        return len(self._store)


class InMemoryLoanRepository(LoanRepository):
    def __init__(self):
        self._store: Dict[str, Loan] = {}

    def save(self, entity: Loan) -> Loan:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Loan]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Loan]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def find_by_user(self, user_id: str) -> List[Loan]:
        return [l for l in self._store.values() if l.user_id == user_id]

    def find_by_book(self, book_id: str) -> List[Loan]:
        return [l for l in self._store.values() if l.book_id == book_id]

    def find_active(self) -> List[Loan]:
        return [l for l in self._store.values() if l.status in (LoanStatus.ACTIVE, LoanStatus.OVERDUE)]

    def find_overdue(self) -> List[Loan]:
        return [l for l in self._store.values() if l.is_overdue() and l.status != LoanStatus.RETURNED]

    def find_active_by_user_and_book(self, user_id: str, book_id: str) -> Optional[Loan]:
        return next(
            (l for l in self._store.values()
             if l.user_id == user_id and l.book_id == book_id
             and l.status in (LoanStatus.ACTIVE, LoanStatus.OVERDUE)),
            None,
        )

    def count(self) -> int:
        return len(self._store)


class InMemoryNotificationRepository(NotificationRepository):
    def __init__(self):
        self._store: Dict[str, Notification] = {}

    def save(self, entity: Notification) -> Notification:
        self._store[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: str) -> Optional[Notification]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Notification]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def find_by_user(self, user_id: str) -> List[Notification]:
        return [n for n in self._store.values() if n.user_id == user_id]

    def find_unread_by_user(self, user_id: str) -> List[Notification]:
        return [n for n in self._store.values() if n.user_id == user_id and not n.read]

    def count(self) -> int:
        return len(self._store)
