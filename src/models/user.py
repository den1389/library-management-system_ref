"""User domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(Enum):
    READER = "reader"
    LIBRARIAN = "librarian"


class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"


@dataclass
class User:
    id: str
    name: str
    email: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    borrowed_books: list = field(default_factory=list)
    reserved_books: list = field(default_factory=list)
    fine_amount: float = 0.0
    borrow_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    MAX_BORROW_LIMIT = 5
    MAX_FINE_BEFORE_BLOCK = 50.0

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_blocked(self) -> bool:
        return self.status == UserStatus.BLOCKED

    def can_borrow(self) -> bool:
        return (
            self.is_active()
            and len(self.borrowed_books) < self.MAX_BORROW_LIMIT
            and self.fine_amount < self.MAX_FINE_BEFORE_BLOCK
        )

    def block(self) -> None:
        self.status = UserStatus.BLOCKED

    def unblock(self) -> None:
        self.status = UserStatus.ACTIVE

    def add_fine(self, amount: float) -> None:
        self.fine_amount += amount
        if self.fine_amount >= self.MAX_FINE_BEFORE_BLOCK:
            self.block()

    def pay_fine(self, amount: float) -> float:
        paid = min(amount, self.fine_amount)
        self.fine_amount -= paid
        if self.fine_amount < self.MAX_FINE_BEFORE_BLOCK and self.is_blocked():
            self.unblock()
        return paid

    def add_borrowed_book(self, book_id: str) -> None:
        if book_id not in self.borrowed_books:
            self.borrowed_books.append(book_id)
            self.borrow_count += 1

    def remove_borrowed_book(self, book_id: str) -> None:
        if book_id in self.borrowed_books:
            self.borrowed_books.remove(book_id)

    def add_reserved_book(self, book_id: str) -> None:
        if book_id not in self.reserved_books:
            self.reserved_books.append(book_id)

    def remove_reserved_book(self, book_id: str) -> None:
        if book_id in self.reserved_books:
            self.reserved_books.remove(book_id)

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', role={self.role.value}, status={self.status.value})"
