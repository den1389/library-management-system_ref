"""Abstract repository interfaces (Dependency Inversion Principle)."""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass

    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        pass


class BookRepository(Repository):
    """Book-specific repository interface."""

    @abstractmethod
    def find_by_isbn(self, isbn: str) -> Optional[object]:
        pass

    @abstractmethod
    def find_by_author(self, author: str) -> List[object]:
        pass

    @abstractmethod
    def find_by_genre(self, genre: str) -> List[object]:
        pass

    @abstractmethod
    def find_available(self) -> List[object]:
        pass

    @abstractmethod
    def search(self, query: str) -> List[object]:
        pass


class UserRepository(Repository):
    """User-specific repository interface."""

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[object]:
        pass

    @abstractmethod
    def find_by_role(self, role: str) -> List[object]:
        pass

    @abstractmethod
    def find_blocked(self) -> List[object]:
        pass


class LoanRepository(Repository):
    """Loan-specific repository interface."""

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[object]:
        pass

    @abstractmethod
    def find_by_book(self, book_id: str) -> List[object]:
        pass

    @abstractmethod
    def find_active(self) -> List[object]:
        pass

    @abstractmethod
    def find_overdue(self) -> List[object]:
        pass

    @abstractmethod
    def find_active_by_user_and_book(self, user_id: str, book_id: str) -> Optional[object]:
        pass


class NotificationRepository(Repository):
    """Notification-specific repository interface."""

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[object]:
        pass

    @abstractmethod
    def find_unread_by_user(self, user_id: str) -> List[object]:
        pass
