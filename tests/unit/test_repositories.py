"""Unit tests for in-memory repositories."""
import pytest
from src.models.book import Book, BookStatus
from src.models.user import User, UserRole, UserStatus
from src.models.loan import Loan, LoanStatus
from src.models.notification import Notification, NotificationType
from src.storage.in_memory import (
    InMemoryBookRepository, InMemoryUserRepository,
    InMemoryLoanRepository, InMemoryNotificationRepository,
)
from tests.conftest import make_book, make_user, make_loan
import uuid


def make_notif(nid=None, user_id="u1", read=False):
    return Notification(
        id=nid or str(uuid.uuid4()),
        user_id=user_id,
        type=NotificationType.OVERDUE_REMINDER,
        message="test",
        read=read,
    )


class TestInMemoryBookRepository:
    def test_save_and_find_by_id(self, book_repo):
        b = make_book()
        book_repo.save(b)
        assert book_repo.find_by_id("b1") == b

    def test_find_by_id_missing(self, book_repo):
        assert book_repo.find_by_id("nonexistent") is None

    def test_find_all_empty(self, book_repo):
        assert book_repo.find_all() == []

    def test_find_all_returns_all(self, book_repo):
        book_repo.save(make_book("b1"))
        book_repo.save(make_book("b2"))
        assert len(book_repo.find_all()) == 2

    def test_delete_existing(self, book_repo):
        book_repo.save(make_book())
        assert book_repo.delete("b1") is True
        assert book_repo.find_by_id("b1") is None

    def test_delete_nonexistent(self, book_repo):
        assert book_repo.delete("nope") is False

    def test_exists_true(self, book_repo):
        book_repo.save(make_book())
        assert book_repo.exists("b1") is True

    def test_exists_false(self, book_repo):
        assert book_repo.exists("nope") is False

    def test_find_by_isbn(self, book_repo):
        b = make_book(isbn="978-3-16-148410-0")
        book_repo.save(b)
        assert book_repo.find_by_isbn("978-3-16-148410-0") == b

    def test_find_by_isbn_not_found(self, book_repo):
        assert book_repo.find_by_isbn("0000") is None

    def test_find_by_author(self, book_repo):
        book_repo.save(make_book("b1", author="Taras Shevchenko"))
        book_repo.save(make_book("b2", author="Ivan Franko"))
        results = book_repo.find_by_author("Taras")
        assert len(results) == 1

    def test_find_by_author_case_insensitive(self, book_repo):
        book_repo.save(make_book("b1", author="Author One"))
        results = book_repo.find_by_author("author one")
        assert len(results) == 1

    def test_find_by_genre(self, book_repo):
        book_repo.save(make_book("b1", genre="Fiction"))
        book_repo.save(make_book("b2", genre="Science"))
        assert len(book_repo.find_by_genre("Fiction")) == 1

    def test_find_by_genre_case_insensitive(self, book_repo):
        book_repo.save(make_book("b1", genre="Fiction"))
        assert len(book_repo.find_by_genre("fiction")) == 1

    def test_find_available(self, book_repo):
        book_repo.save(make_book("b1", status=BookStatus.AVAILABLE))
        book_repo.save(make_book("b2", status=BookStatus.BORROWED))
        assert len(book_repo.find_available()) == 1

    def test_search_by_title(self, book_repo):
        book_repo.save(make_book("b1", title="Python Programming"))
        results = book_repo.search("python")
        assert len(results) == 1

    def test_search_by_author(self, book_repo):
        book_repo.save(make_book("b1", author="Guido van Rossum"))
        results = book_repo.search("Guido")
        assert len(results) == 1

    def test_search_by_isbn(self, book_repo):
        book_repo.save(make_book("b1", isbn="1234567890"))
        results = book_repo.search("1234567890")
        assert len(results) == 1

    def test_search_no_results(self, book_repo):
        book_repo.save(make_book())
        results = book_repo.search("zzznomatch")
        assert len(results) == 0

    def test_count(self, book_repo):
        book_repo.save(make_book("b1"))
        book_repo.save(make_book("b2"))
        assert book_repo.count() == 2

    def test_save_updates_existing(self, book_repo):
        b = make_book()
        book_repo.save(b)
        b.title = "Updated Title"
        book_repo.save(b)
        assert book_repo.find_by_id("b1").title == "Updated Title"


class TestInMemoryUserRepository:
    def test_save_and_find(self, user_repo):
        u = make_user()
        user_repo.save(u)
        assert user_repo.find_by_id("u1") == u

    def test_find_by_email(self, user_repo):
        u = make_user(email="test@test.com")
        user_repo.save(u)
        assert user_repo.find_by_email("test@test.com") == u

    def test_find_by_email_not_found(self, user_repo):
        assert user_repo.find_by_email("nope@nope.com") is None

    def test_find_by_role_reader(self, user_repo):
        user_repo.save(make_user("u1", role=UserRole.READER))
        user_repo.save(make_user("u2", role=UserRole.LIBRARIAN))
        readers = user_repo.find_by_role("reader")
        assert len(readers) == 1

    def test_find_blocked(self, user_repo):
        user_repo.save(make_user("u1", status=UserStatus.ACTIVE))
        user_repo.save(make_user("u2", status=UserStatus.BLOCKED))
        blocked = user_repo.find_blocked()
        assert len(blocked) == 1

    def test_delete(self, user_repo):
        user_repo.save(make_user())
        assert user_repo.delete("u1") is True
        assert user_repo.find_by_id("u1") is None

    def test_exists(self, user_repo):
        user_repo.save(make_user())
        assert user_repo.exists("u1") is True


class TestInMemoryLoanRepository:
    def test_save_and_find(self, loan_repo):
        l = make_loan()
        loan_repo.save(l)
        assert loan_repo.find_by_id("l1") == l

    def test_find_by_user(self, loan_repo):
        loan_repo.save(make_loan("l1", user_id="u1"))
        loan_repo.save(make_loan("l2", user_id="u2"))
        assert len(loan_repo.find_by_user("u1")) == 1

    def test_find_by_book(self, loan_repo):
        loan_repo.save(make_loan("l1", book_id="b1"))
        loan_repo.save(make_loan("l2", book_id="b2"))
        assert len(loan_repo.find_by_book("b1")) == 1

    def test_find_active(self, loan_repo):
        active = make_loan("l1")
        active.status = LoanStatus.ACTIVE
        returned = make_loan("l2")
        returned.status = LoanStatus.RETURNED
        loan_repo.save(active)
        loan_repo.save(returned)
        assert len(loan_repo.find_active()) == 1

    def test_find_overdue(self, loan_repo):
        overdue_loan = make_loan("l1", overdue_days=5)
        not_overdue = make_loan("l2", days_until_due=5)
        loan_repo.save(overdue_loan)
        loan_repo.save(not_overdue)
        assert len(loan_repo.find_overdue()) == 1

    def test_find_active_by_user_and_book(self, loan_repo):
        l = make_loan("l1", user_id="u1", book_id="b1")
        loan_repo.save(l)
        result = loan_repo.find_active_by_user_and_book("u1", "b1")
        assert result == l

    def test_find_active_by_user_and_book_not_found(self, loan_repo):
        result = loan_repo.find_active_by_user_and_book("u999", "b999")
        assert result is None


class TestInMemoryNotificationRepository:
    def test_save_and_find(self, notification_repo):
        n = make_notif("n1")
        notification_repo.save(n)
        assert notification_repo.find_by_id("n1") == n

    def test_find_by_user(self, notification_repo):
        notification_repo.save(make_notif(user_id="u1"))
        notification_repo.save(make_notif(user_id="u2"))
        assert len(notification_repo.find_by_user("u1")) == 1

    def test_find_unread_by_user(self, notification_repo):
        notification_repo.save(make_notif(user_id="u1", read=False))
        notification_repo.save(make_notif(user_id="u1", read=True))
        unread = notification_repo.find_unread_by_user("u1")
        assert len(unread) == 1

    def test_delete(self, notification_repo):
        n = make_notif("n1")
        notification_repo.save(n)
        assert notification_repo.delete("n1") is True
