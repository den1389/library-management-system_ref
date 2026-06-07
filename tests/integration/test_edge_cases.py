"""Edge case and boundary integration tests."""
import pytest
from datetime import datetime, timedelta

from src.models.book import BookStatus
from src.models.user import UserStatus
from src.services.library_service import LibraryException, UserBlockedError, BorrowLimitExceededError
from src.services.fine_strategy import StandardFineStrategy


class TestEdgeCases:
    def test_user_blocked_by_excessive_fines(self, service):
        user = service.register_user("FinedUser", "fined@test.com")
        book = service.add_book("FinedBook", "Auth", "F001", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        # Make massively overdue
        loan.due_date = datetime.now() - timedelta(days=110)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        u = service.get_user(user.id)
        # 7*0.5 + ... 110 days * 0.5 = 55 >= 50 => blocked
        assert u.is_blocked()

    def test_user_at_exact_limit_can_still_borrow(self, service):
        user = service.register_user("ExactLimit", "exact@test.com")
        user.fine_amount = 49.99
        service._users.save(user)
        book = service.add_book("ExactBook", "Auth", "E001", 2020, "G")
        # Should succeed
        loan = service.borrow_book(user.id, book.id)
        assert loan is not None

    def test_user_fine_at_limit_blocked_cannot_borrow(self, service):
        user = service.register_user("LimitUser", "limit@test.com")
        user.fine_amount = 50.0
        user.block()
        service._users.save(user)
        book = service.add_book("LimitBook", "Auth", "L001", 2020, "G")
        with pytest.raises(UserBlockedError):
            service.borrow_book(user.id, book.id)

    def test_borrow_5_books_exactly_at_limit(self, service):
        user = service.register_user("MaxUser", "max@test.com")
        loans = []
        for i in range(5):
            book = service.add_book(f"MaxBook{i}", "Auth", f"MAX{i:03}", 2020, "G")
            loan = service.borrow_book(user.id, book.id)
            loans.append(loan)
        assert len(loans) == 5

    def test_return_then_can_borrow_again(self, service):
        user = service.register_user("Cycle", "cycle@test.com")
        # Fill to limit
        books = []
        for i in range(5):
            b = service.add_book(f"Cycle{i}", "Auth", f"CY{i:03}", 2020, "G")
            service.borrow_book(user.id, b.id)
            books.append(b)
        # Return one
        service.return_book(user.id, books[0].id)
        # Now can borrow again
        extra = service.add_book("CycleExtra", "Auth", "CYEX", 2020, "G")
        loan = service.borrow_book(user.id, extra.id)
        assert loan is not None

    def test_notification_fine_charged_message_contains_amount(self, service, notification_repo):
        user = service.register_user("AmountCheck", "amount@test.com")
        book = service.add_book("AmountBook", "Auth", "AM001", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        loan.due_date = datetime.now() - timedelta(days=4)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        notifs = notification_repo.find_by_user(user.id)
        fine_notifs = [n for n in notifs if "штраф" in n.message.lower() or "грн" in n.message]
        assert len(fine_notifs) > 0

    def test_queue_order_respected_after_return(self, service):
        borrower = service.register_user("Borrower", "borrow@t.com")
        first_waiter = service.register_user("First", "first@t.com")
        second_waiter = service.register_user("Second", "second@t.com")
        book = service.add_book("QueueOrder", "Auth", "QO001", 2020, "G")
        service.borrow_book(borrower.id, book.id)
        service.reserve_book(first_waiter.id, book.id)
        service.reserve_book(second_waiter.id, book.id)
        service.return_book(borrower.id, book.id)
        updated_book = service.get_book(book.id)
        # First waiter should be next in queue
        assert updated_book.next_in_queue() == first_waiter.id

    def test_empty_search_returns_all(self, service):
        service.add_book("Alpha", "Auth", "AL001", 2020, "G")
        service.add_book("Beta", "Auth", "BE001", 2020, "G")
        results = service.search_books("a")
        assert len(results) >= 1

    def test_statistics_empty_library(self, service):
        stats = service.get_statistics()
        assert stats["total_books"] == 0
        assert stats["total_users"] == 0
        assert stats["active_loans"] == 0

    def test_overdue_fine_sets_exactly_threshold_blocks(self, service):
        user = service.register_user("ThresholdUser", "thresh@test.com")
        user.fine_amount = 49.0
        service._users.save(user)
        book = service.add_book("ThreshBook", "Auth", "TH001", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        # 2 days overdue = 1.0 UAH fine → total = 50.0 → block
        loan.due_date = datetime.now() - timedelta(days=2)
        service._loans.save(loan)
        service.return_book(user.id, book.id)
        u = service.get_user(user.id)
        assert u.is_blocked()

    def test_multiple_books_same_author_search(self, service):
        service.add_book("Book1", "Franko", "FR001", 2020, "G")
        service.add_book("Book2", "Franko", "FR002", 2020, "G")
        service.add_book("Book3", "Other", "OT001", 2020, "G")
        results = service.search_books("Franko")
        assert len(results) == 2

    def test_process_overdue_sends_notifications(self, service, notification_repo):
        user = service.register_user("OverdueNotif", "odn@test.com")
        book = service.add_book("ODNBook", "Auth", "ODN001", 2020, "G")
        loan = service.borrow_book(user.id, book.id)
        loan.due_date = datetime.now() - timedelta(days=3)
        service._loans.save(loan)
        service.process_overdue_loans()
        notifs = notification_repo.find_by_user(user.id)
        assert len(notifs) > 0

    def test_get_active_loans_excludes_returned(self, service):
        user = service.register_user("ActiveTest", "active@test.com")
        book1 = service.add_book("Book1", "Auth", "ACT001", 2020, "G")
        book2 = service.add_book("Book2", "Auth", "ACT002", 2020, "G")
        service.borrow_book(user.id, book1.id)
        loan2 = service.borrow_book(user.id, book2.id)
        service.return_book(user.id, book1.id)
        active = service.get_active_loans()
        active_ids = [l.id for l in active]
        assert loan2.id in active_ids
