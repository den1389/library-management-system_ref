"""Notification domain model."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NotificationType(Enum):
    BOOK_AVAILABLE = "book_available"
    OVERDUE_REMINDER = "overdue_reminder"
    FINE_CHARGED = "fine_charged"
    RESERVATION_READY = "reservation_ready"
    ACCOUNT_BLOCKED = "account_blocked"
    LOAN_EXTENDED = "loan_extended"
    BOOK_RETURNED = "book_returned"


@dataclass
class Notification:
    id: str
    user_id: str
    type: NotificationType
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    read: bool = False

    def mark_read(self) -> None:
        self.read = True

    def __repr__(self) -> str:
        return f"Notification(id={self.id}, user={self.user_id}, type={self.type.value})"
