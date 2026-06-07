"""Integration tests — reservations, user management, fines."""
import pytest
from datetime import timedelta

from src.models.book import BookStatus
from src.models.user import UserStatus
from src.services.library_service import (
    LibraryService, LibraryException, UserBlockedError, BookNotFoundError
)
from src.services.fine_strategy import ProgressiveFineStrategy, FlatFineStrategy, WeeklyFineStrategy


class TestReservations:
    def test_reserve_borrowed_book(self, service):
        u1 = service.register_user("A", "a@t.com")
        u2 = service.register_user("B", "b@t.com")
        book = service.add_book("T", "Auth", "I001", 2020, "G")
        service.borrow_book(u1.id, book.id)
        service.reserve_book(u2.id, book.id)
        updated = service.get_book(book.id)
        assert u2.id in updated.reservation_queue

    def test_reserve_available_book_raises(self, service):
        u = service.register_user("C", "c@t.com")
        book = service.add_book("T", "Auth", "I002", 2020, "G")
        with pytest.raises(LibraryException):
            service.reserve_book(u.id, book.id)

    def test_duplicate_reservation_raises(self, service):
        u1 = service.register_user("D", "d@t.com")
        u2 = service.register_user("E", "e@t.com")
        book = service.add_book("T", "Auth", "I003", 2020, "G")
        service.borrow_book(u1.id, book.id)
        service.reserve_book(u2.id, book.id)
        with pytest.raises(LibraryException):
            service.reserve_book(u2.id, book.id)

    def test_blocked_user_cannot_reserve(self, service):
        u1 = service.register_user("F", "f@t.com")
        u2 = service.register_user("G", "g@t.com")
        service.block_user(u2.id)
        book = service.add_book("T", "Auth", "I004", 2020, "G")
        service.borrow_book(u1.id, book.id)
        with pytest.raises(UserBlockedError):
            service.reserve_book(u2.id, book.id)

    def test_cancel_reservation(self, service):
        u1 = service.register_user("H", "h@t.com")
        u2 = service.register_user("I", "i@t.com")
        book = service.add_book("T", "Auth", "I005", 2020, "G")
        service.borrow_book(u1.id, book.id)
        service.reserve_book(u2.id, book.id)
        service.cancel_reservation(u2.id, book.id)
        updated = service.get_book(book.id)
        assert u2.id not in updated.reservation_queue

    def test_cancel_last_reservation_makes_available(self, service):
        u1 = service.register_user("J", "j@t.com")
        u2 = service.register_user("K", "k@t.com")
        book = service.add_book("T", "Auth", "I006", 2020, "G")
        service.borrow_book(u1.id, book.id)
        service.reserve_book(u2.id, book.id)
        service.return_book(u1.id, book.id)
        service.cancel_reservation(u2.id, book.id)
        assert service.get_book(book.id).status == BookStatus.AVAILABLE

    def test_multiple_users_queue(self, service):
        u1 = service.register_user("L", "l@t.com")
        borrower = service.register_user("Borrower", "borrower@t.com")
        book = service.add_book("Popular", "Auth", "I007", 2020, "G")
        service.borrow_book(borrower.id, book.id)
        waiters = []
        for i in range(3):
            u = service.register_user(f"Waiter{i}", f"w{i}@t.com")
            service.reserve_book(u.id, book.id)
            waiters.append(u)
        updated = service.get_book(book.id)
        assert len(updated.reservation_queue) == 3


class TestUserManagement:
    def test_register_user(self, service):
        user = service.register_user("Test", "test@test.com")
        assert user.id is not None

    def test_duplicate_email_raises(self, service):
        service.register_user("A", "same@test.com")
        with pytest.raises(LibraryException):
            service.register_user("B", "same@test.com")

    def test_block_user_manually(self, service):
        user = service.register_user("Block", "block@test.com")
        service.block_user(user.id)
        assert service.get_user(user.id).is_blocked()

    def test_unblock_user(self, service):
        user = service.register_user("Unblock", "unblock@test.com")
        service.block_user(user.id)
        service.unblock_user(user.id)
        assert service.get_user(user.id).is_active()

    def test_pay_fine_reduces_amount(self, service):
        user = service.register_user("Payer", "payer@test.com")
        user.fine_amount = 30.0
        service._users.save(user)
        service.pay_fine(user.id, 15.0)
        assert service.get_user(user.id).fine_amount == 15.0

    def test_pay_fine_unblocks_user(self, service):
        user = service.register_user("PayUnblock", "payunblock@test.com")
        user.fine_amount = 60.0
        user.block()
        service._users.save(user)
        service.pay_fine(user.id, 20.0)
        assert service.get_user(user.id).is_active()

    def test_get_nonexistent_user_raises(self, service):
        with pytest.raises(Exception):
            service.get_user("nope")

    def test_block_sends_notification(self, service, notification_repo):
        user = service.register_user("NotifUser", "notifuser@test.com")
        service.block_user(user.id)
        notifs = notification_repo.find_by_user(user.id)
        assert len(notifs) > 0


class TestFineStrategies:
    def test_service_uses_standard_by_default(self, service):
        assert service._fine_calc.strategy_name() == "standard"

    def test_switch_to_progressive_strategy(self, service):
        service.set_fine_strategy(ProgressiveFineStrategy())
        assert service._fine_calc.strategy_name() == "progressive"

    def test_switch_to_flat_strategy(self, service):
        service.set_fine_strategy(FlatFineStrategy())
        assert service._fine_calc.strategy_name() == "flat"

    def test_switch_to_weekly_strategy(self, service):
        service.set_fine_strategy(WeeklyFineStrategy())
        assert service._fine_calc.strategy_name() == "weekly"

    def test_flat_strategy_charges_fixed_fine(self, service):
        from datetime import datetime
        service.set_fine_strategy(FlatFineStrategy())
        user = service.register_user("FlatUser", "flat@test.com")
        book = service.add_book("FlatBook", "Author", "FLAT01", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        loan.due_date = datetime.now() - timedelta(days=10)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        u = service.get_user(user.id)
        assert u.fine_amount == 5.0

    def test_progressive_strategy_higher_fine_long_overdue(self, service):
        from datetime import datetime
        service.set_fine_strategy(ProgressiveFineStrategy())
        user = service.register_user("ProgUser", "prog@test.com")
        book = service.add_book("ProgBook", "Author", "PROG01", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        loan.due_date = datetime.now() - timedelta(days=20)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        u = service.get_user(user.id)
        # 7*0.5 + 7*1.0 + 6*2.0 = 3.5+7+12 = 22.5
        assert u.fine_amount == 22.5


class TestStatistics:
    def test_statistics_default(self, service):
        stats = service.get_statistics()
        assert "total_books" in stats
        assert "total_users" in stats
        assert "active_loans" in stats

    def test_statistics_after_actions(self, service):
        user = service.register_user("StatUser", "stat@test.com")
        book = service.add_book("StatBook", "Author", "STAT01", 2020, "G")
        service.borrow_book(user.id, book.id)
        stats = service.get_statistics()
        assert stats["total_books"] == 1
        assert stats["total_users"] == 1
        assert stats["active_loans"] == 1
        assert stats["available_books"] == 0

    def test_search_books(self, service):
        service.add_book("Python Cookbook", "Author", "PY001", 2020, "Tech")
        results = service.search_books("Python")
        assert len(results) == 1

    def test_list_available_books(self, service):
        service.add_book("Available", "Author", "AV001", 2020, "G")
        books = service.list_available_books()
        assert len(books) == 1

    def test_process_overdue_loans(self, service):
        from datetime import datetime
        user = service.register_user("OverdueUser", "overdue@test.com")
        book = service.add_book("OverdueBook", "Author", "OD001", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        loan.due_date = datetime.now() - timedelta(days=3)
        service._loans.save(loan)
        processed = service.process_overdue_loans()
        assert len(processed) == 1


class TestBookManagement:
    def test_add_book(self, service):
        book = service.add_book("New Book", "Auth", "NB001", 2021, "Sci")
        assert book.id is not None

    def test_add_duplicate_isbn_raises(self, service):
        service.add_book("Book1", "Auth", "DUP001", 2020, "G")
        with pytest.raises(LibraryException):
            service.add_book("Book2", "Auth", "DUP001", 2021, "G")

    def test_remove_available_book(self, service):
        book = service.add_book("ToRemove", "Auth", "RM001", 2020, "G")
        result = service.remove_book(book.id)
        assert result is True

    def test_remove_borrowed_book_raises(self, service):
        user = service.register_user("RemoveUser", "remove@test.com")
        book = service.add_book("BorrowedBook", "Auth", "RB001", 2020, "G")
        service.borrow_book(user.id, book.id)
        with pytest.raises(LibraryException):
            service.remove_book(book.id)

    def test_remove_nonexistent_book_raises(self, service):
        with pytest.raises(BookNotFoundError):
            service.remove_book("nonexistent")

    def test_list_all_books(self, service):
        service.add_book("B1", "A", "LA001", 2020, "G")
        service.add_book("B2", "A", "LA002", 2020, "G")
        assert len(service.list_all_books()) == 2

    def test_get_user_loans(self, service):
        user = service.register_user("LoanUser", "loan@test.com")
        book = service.add_book("LoanBook", "Auth", "LB001", 2020, "G")
        service.borrow_book(user.id, book.id)
        loans = service.get_user_loans(user.id)
        assert len(loans) == 1
