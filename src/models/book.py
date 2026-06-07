"""Book domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class BookStatus(Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    LOST = "lost"


@dataclass
class Book:
    id: str
    title: str
    author: str
    isbn: str
    year: int
    genre: str
    status: BookStatus = BookStatus.AVAILABLE
    borrower_id: Optional[str] = None
    due_date: Optional[datetime] = None
    reservation_queue: list = field(default_factory=list)

    def is_available(self) -> bool:
        return self.status == BookStatus.AVAILABLE

    def is_borrowed(self) -> bool:
        return self.status == BookStatus.BORROWED

    def is_reserved(self) -> bool:
        return self.status == BookStatus.RESERVED

    def has_reservation_queue(self) -> bool:
        return len(self.reservation_queue) > 0

    def add_to_queue(self, user_id: str) -> None:
        if user_id not in self.reservation_queue:
            self.reservation_queue.append(user_id)

    def remove_from_queue(self, user_id: str) -> None:
        if user_id in self.reservation_queue:
            self.reservation_queue.remove(user_id)

    def next_in_queue(self) -> Optional[str]:
        return self.reservation_queue[0] if self.reservation_queue else None

    def __repr__(self) -> str:
        return f"Book(id={self.id}, title='{self.title}', status={self.status.value})"
