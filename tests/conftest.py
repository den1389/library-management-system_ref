"""Shared test fixtures."""
import pytest
from datetime import datetime, timedelta

from src.models.book import Book, BookStatus
from src.models.user import User, UserRole, UserStatus
from src.models.loan import Loan, LoanStatus
from src.services.library_service import LibraryService
from src.services.fine_strategy import StandardFineStrategy, ProgressiveFineStrategy
from src.storage.in_memory import (
    InMemoryBookRepository,
    InMemoryUserRepository,
    InMemoryLoanRepository,
    InMemoryNotificationRepository,
)


def make_book(book_id="b1", title="Test Book", author="Author", isbn="1234567890",
              year=2020, genre="Fiction", status=BookStatus.AVAILABLE):
    return Book(id=book_id, title=title, author=author, isbn=isbn,
                year=year, genre=genre, status=status)


def make_user(user_id="u1", name="John Doe", email="john@test.com",
              role=UserRole.READER, status=UserStatus.ACTIVE):
    return User(id=user_id, name=name, email=email, role=role, status=status)


def make_loan(loan_id="l1", book_id="b1", user_id="u1",
              days_until_due=14, overdue_days=0):
    if overdue_days > 0:
        due = datetime.now() - timedelta(days=overdue_days)
    else:
        due = datetime.now() + timedelta(days=days_until_due)
    return Loan(id=loan_id, book_id=book_id, user_id=user_id,
                due_date=due, status=LoanStatus.ACTIVE)


@pytest.fixture
def book_repo():
    return InMemoryBookRepository()


@pytest.fixture
def user_repo():
    return InMemoryUserRepository()


@pytest.fixture
def loan_repo():
    return InMemoryLoanRepository()


@pytest.fixture
def notification_repo():
    return InMemoryNotificationRepository()


@pytest.fixture
def service(book_repo, user_repo, loan_repo, notification_repo):
    return LibraryService(
        book_repo=book_repo,
        user_repo=user_repo,
        loan_repo=loan_repo,
        notification_repo=notification_repo,
        fine_strategy=StandardFineStrategy(),
    )


@pytest.fixture
def sample_book(book_repo):
    b = make_book()
    return book_repo.save(b)


@pytest.fixture
def sample_user(user_repo):
    u = make_user()
    return user_repo.save(u)


@pytest.fixture
def sample_loan(loan_repo, sample_book, sample_user):
    sample_book.status = BookStatus.BORROWED
    l = make_loan(book_id=sample_book.id, user_id=sample_user.id)
    return loan_repo.save(l)
