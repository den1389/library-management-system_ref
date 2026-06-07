"""Integration tests — borrow and return workflows."""
import pytest
from datetime import datetime, timedelta

from src.models.book import BookStatus
from src.models.loan import LoanStatus
from src.models.user import UserRole, UserStatus
from src.services.library_service import (
    LibraryService, BookNotAvailableError, UserBlockedError,
    BorrowLimitExceededError, BookNotFoundError, UserNotFoundError,
    LoanNotFoundError, AlreadyBorrowedError, LibraryException,
)
from src.services.fine_strategy import ProgressiveFineStrategy, FlatFineStrategy


class TestBorrowBook:
    def test_borrow_available_book(self, service):
        user = service.register_user("Alice", "alice@test.com")
        book = service.add_book("Python", "Author", "ISBN001", 2020, "Tech")
        loan = service.borrow_book(user.id, book.id)
        assert loan is not None
        assert loan.user_id == user.id
        assert loan.book_id == book.id

    def test_book_becomes_borrowed_after_loan(self, service):
        user = service.register_user("Bob", "bob@test.com")
        book = service.add_book("Java", "Author", "ISBN002", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        updated_book = service.get_book(book.id)
        assert updated_book.status == BookStatus.BORROWED

    def test_user_borrowed_books_updated(self, service):
        user = service.register_user("Carol", "carol@test.com")
        book = service.add_book("Go", "Author", "ISBN003", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        updated_user = service.get_user(user.id)
        assert book.id in updated_user.borrowed_books

    def test_borrow_unavailable_book_raises(self, service):
        user = service.register_user("Dave", "dave@test.com")
        book = service.add_book("Rust", "Author", "ISBN004", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        user2 = service.register_user("Eve", "eve@test.com")
        with pytest.raises(BookNotAvailableError):
            service.borrow_book(user2.id, book.id)

    def test_blocked_user_cannot_borrow(self, service):
        user = service.register_user("Frank", "frank@test.com")
        service.block_user(user.id)
        book = service.add_book("Blocked Book", "Author", "ISBN005", 2020, "Tech")
        with pytest.raises(UserBlockedError):
            service.borrow_book(user.id, book.id)

    def test_user_at_borrow_limit_cannot_borrow(self, service):
        user = service.register_user("Grace", "grace@test.com")
        books = []
        for i in range(5):
            b = service.add_book(f"Book{i}", "Author", f"ISBN{i:03}", 2020, "Tech")
            service.borrow_book(user.id, b.id)
            books.append(b)
        extra = service.add_book("Extra", "Author", "ISBN999", 2020, "Tech")
        with pytest.raises(BorrowLimitExceededError):
            service.borrow_book(user.id, extra.id)

    def test_already_borrowed_same_book_raises(self, service):
        user = service.register_user("Hank", "hank@test.com")
        book = service.add_book("Double", "Author", "ISBN006", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        with pytest.raises((BookNotAvailableError, AlreadyBorrowedError)):
            service.borrow_book(user.id, book.id)

    def test_borrow_nonexistent_book_raises(self, service):
        user = service.register_user("Ivy", "ivy@test.com")
        with pytest.raises(BookNotFoundError):
            service.borrow_book(user.id, "nonexistent_book_id")

    def test_borrow_nonexistent_user_raises(self, service):
        book = service.add_book("UserlessBook", "Author", "ISBN007", 2020, "Tech")
        with pytest.raises(UserNotFoundError):
            service.borrow_book("nonexistent_user_id", book.id)

    def test_custom_loan_duration(self, service):
        user = service.register_user("Jake", "jake@test.com")
        book = service.add_book("Custom", "Author", "ISBN008", 2020, "Tech")
        loan = service.borrow_book(user.id, book.id, days=7)
        expected = datetime.now() + timedelta(days=7)
        diff = abs((loan.due_date - expected).total_seconds())
        assert diff < 5  # within 5 seconds

    def test_borrow_count_increments(self, service):
        user = service.register_user("Kara", "kara@test.com")
        book = service.add_book("Count", "Author", "ISBN009", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        updated = service.get_user(user.id)
        assert updated.borrow_count == 1


class TestReturnBook:
    def test_return_book_success(self, service):
        user = service.register_user("Leo", "leo@test.com")
        book = service.add_book("ReturnTest", "Author", "ISBN010", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        loan = service.return_book(user.id, book.id)
        assert loan.status == LoanStatus.RETURNED

    def test_book_available_after_return(self, service):
        user = service.register_user("Mia", "mia@test.com")
        book = service.add_book("BackOnShelf", "Author", "ISBN011", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        service.return_book(user.id, book.id)
        assert service.get_book(book.id).status == BookStatus.AVAILABLE

    def test_user_borrowed_books_updated_on_return(self, service):
        user = service.register_user("Nick", "nick@test.com")
        book = service.add_book("UserUpdate", "Author", "ISBN012", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        service.return_book(user.id, book.id)
        assert book.id not in service.get_user(user.id).borrowed_books

    def test_return_overdue_charges_fine(self, service):
        from tests.conftest import make_loan
        user = service.register_user("Olivia", "olivia@test.com")
        book = service.add_book("Overdue", "Author", "ISBN013", 2020, "Tech")
        loan = service.borrow_book(user.id, book.id)
        # Manually make loan overdue
        loan.due_date = datetime.now() - timedelta(days=5)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        updated_user = service.get_user(user.id)
        assert updated_user.fine_amount > 0

    def test_return_nonexistent_loan_raises(self, service):
        user = service.register_user("Paul", "paul@test.com")
        book = service.add_book("NoLoan", "Author", "ISBN014", 2020, "Tech")
        with pytest.raises(LoanNotFoundError):
            service.return_book(user.id, book.id)

    def test_return_creates_notification(self, service, notification_repo):
        user = service.register_user("Quinn", "quinn@test.com")
        book = service.add_book("NotifTest", "Author", "ISBN015", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        service.return_book(user.id, book.id)
        notifs = notification_repo.find_by_user(user.id)
        assert len(notifs) > 0

    def test_return_book_with_queue_sets_reserved(self, service):
        user1 = service.register_user("Rita", "rita@test.com")
        user2 = service.register_user("Sam", "sam@test.com")
        book = service.add_book("QueueBook", "Author", "ISBN016", 2020, "Tech")
        service.borrow_book(user1.id, book.id)
        service.reserve_book(user2.id, book.id)
        service.return_book(user1.id, book.id)
        assert service.get_book(book.id).status == BookStatus.RESERVED


class TestExtendLoan:
    def test_extend_loan_success(self, service):
        user = service.register_user("Tom", "tom@test.com")
        book = service.add_book("ExtendMe", "Author", "ISBN017", 2020, "Tech")
        loan = service.borrow_book(user.id, book.id)
        original_due = loan.due_date
        extended = service.extend_loan(user.id, book.id)
        assert extended.due_date > original_due

    def test_extend_adds_7_days(self, service):
        user = service.register_user("Uma", "uma@test.com")
        book = service.add_book("Extend7", "Author", "ISBN018", 2020, "Tech")
        loan = service.borrow_book(user.id, book.id)
        original = loan.due_date
        service.extend_loan(user.id, book.id)
        updated = service._loans.find_active_by_user_and_book(user.id, book.id)
        diff = (updated.due_date - original).days
        assert diff == 7

    def test_extend_twice_raises(self, service):
        user = service.register_user("Vera", "vera@test.com")
        book = service.add_book("ExtendTwice", "Author", "ISBN019", 2020, "Tech")
        service.borrow_book(user.id, book.id)
        service.extend_loan(user.id, book.id)
        with pytest.raises(LibraryException):
            service.extend_loan(user.id, book.id)

    def test_extend_no_active_loan_raises(self, service):
        user = service.register_user("Walt", "walt@test.com")
        book = service.add_book("NoExtend", "Author", "ISBN020", 2020, "Tech")
        with pytest.raises(LoanNotFoundError):
            service.extend_loan(user.id, book.id)
