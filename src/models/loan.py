"""Loan domain model."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class LoanStatus(Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"
    LOST = "lost"


@dataclass
class Loan:
    id: str
    book_id: str
    user_id: str
    borrowed_at: datetime = field(default_factory=datetime.now)
    due_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=14))
    returned_at: Optional[datetime] = None
    status: LoanStatus = LoanStatus.ACTIVE
    fine_amount: float = 0.0
    extended: bool = False

    DEFAULT_LOAN_DAYS = 14
    EXTENSION_DAYS = 7

    def is_overdue(self) -> bool:
        if self.status == LoanStatus.RETURNED:
            return False
        return datetime.now() > self.due_date

    def days_overdue(self) -> int:
        if not self.is_overdue():
            return 0
        delta = datetime.now() - self.due_date
        return max(0, delta.days)

    def days_remaining(self) -> int:
        if self.status == LoanStatus.RETURNED:
            return 0
        delta = self.due_date - datetime.now()
        return max(0, delta.days)

    def can_extend(self) -> bool:
        return not self.extended and not self.is_overdue() and self.status == LoanStatus.ACTIVE

    def extend(self) -> None:
        if self.can_extend():
            self.due_date += timedelta(days=self.EXTENSION_DAYS)
            self.extended = True

    def mark_returned(self, returned_at: Optional[datetime] = None) -> None:
        self.returned_at = returned_at or datetime.now()
        self.status = LoanStatus.RETURNED

    def mark_lost(self) -> None:
        self.status = LoanStatus.LOST

    def update_status(self) -> None:
        if self.status == LoanStatus.ACTIVE and self.is_overdue():
            self.status = LoanStatus.OVERDUE

    def __repr__(self) -> str:
        return f"Loan(id={self.id}, book={self.book_id}, user={self.user_id}, status={self.status.value})"
