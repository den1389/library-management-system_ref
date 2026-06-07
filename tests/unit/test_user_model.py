"""Unit tests for User model."""
import pytest
from src.models.user import User, UserRole, UserStatus
from tests.conftest import make_user


class TestUserCreation:
    def test_default_status_active(self):
        u = make_user()
        assert u.status == UserStatus.ACTIVE

    def test_default_fine_zero(self):
        u = make_user()
        assert u.fine_amount == 0.0

    def test_default_borrowed_empty(self):
        u = make_user()
        assert u.borrowed_books == []

    def test_default_reserved_empty(self):
        u = make_user()
        assert u.reserved_books == []

    def test_user_role_reader(self):
        u = make_user(role=UserRole.READER)
        assert u.role == UserRole.READER

    def test_user_role_librarian(self):
        u = make_user(role=UserRole.LIBRARIAN)
        assert u.role == UserRole.LIBRARIAN

    def test_borrow_count_starts_zero(self):
        u = make_user()
        assert u.borrow_count == 0


class TestUserStatusChecks:
    def test_is_active_true(self):
        u = make_user(status=UserStatus.ACTIVE)
        assert u.is_active() is True

    def test_is_active_false_when_blocked(self):
        u = make_user(status=UserStatus.BLOCKED)
        assert u.is_active() is False

    def test_is_blocked_true(self):
        u = make_user(status=UserStatus.BLOCKED)
        assert u.is_blocked() is True

    def test_is_blocked_false_when_active(self):
        u = make_user()
        assert u.is_blocked() is False

    def test_block_changes_status(self):
        u = make_user()
        u.block()
        assert u.is_blocked()

    def test_unblock_changes_status(self):
        u = make_user(status=UserStatus.BLOCKED)
        u.unblock()
        assert u.is_active()


class TestUserCanBorrow:
    def test_active_user_can_borrow(self):
        u = make_user()
        assert u.can_borrow() is True

    def test_blocked_user_cannot_borrow(self):
        u = make_user(status=UserStatus.BLOCKED)
        assert u.can_borrow() is False

    def test_user_at_limit_cannot_borrow(self):
        u = make_user()
        u.borrowed_books = ["b1", "b2", "b3", "b4", "b5"]
        assert u.can_borrow() is False

    def test_user_with_high_fine_cannot_borrow(self):
        u = make_user()
        u.fine_amount = 50.0
        assert u.can_borrow() is False

    def test_user_with_fine_below_limit_can_borrow(self):
        u = make_user()
        u.fine_amount = 49.99
        assert u.can_borrow() is True


class TestUserFines:
    def test_add_fine_increases_amount(self):
        u = make_user()
        u.add_fine(10.0)
        assert u.fine_amount == 10.0

    def test_add_multiple_fines(self):
        u = make_user()
        u.add_fine(5.0)
        u.add_fine(10.0)
        assert u.fine_amount == 15.0

    def test_fine_above_limit_blocks_user(self):
        u = make_user()
        u.add_fine(50.0)
        assert u.is_blocked()

    def test_fine_exactly_at_limit_blocks(self):
        u = make_user()
        u.add_fine(50.0)
        assert u.is_blocked()

    def test_fine_below_limit_does_not_block(self):
        u = make_user()
        u.add_fine(49.99)
        assert u.is_active()

    def test_pay_fine_reduces_amount(self):
        u = make_user()
        u.fine_amount = 20.0
        u.pay_fine(10.0)
        assert u.fine_amount == 10.0

    def test_pay_more_than_owed_capped_at_owed(self):
        u = make_user()
        u.fine_amount = 5.0
        paid = u.pay_fine(100.0)
        assert paid == 5.0
        assert u.fine_amount == 0.0

    def test_pay_fine_unblocks_user(self):
        u = make_user(status=UserStatus.BLOCKED)
        u.fine_amount = 60.0
        u.pay_fine(20.0)
        assert u.is_active()

    def test_pay_fine_returns_paid_amount(self):
        u = make_user()
        u.fine_amount = 30.0
        paid = u.pay_fine(15.0)
        assert paid == 15.0


class TestUserBooks:
    def test_add_borrowed_book(self):
        u = make_user()
        u.add_borrowed_book("b1")
        assert "b1" in u.borrowed_books

    def test_add_same_book_no_duplicate(self):
        u = make_user()
        u.add_borrowed_book("b1")
        u.add_borrowed_book("b1")
        assert u.borrowed_books.count("b1") == 1

    def test_remove_borrowed_book(self):
        u = make_user()
        u.add_borrowed_book("b1")
        u.remove_borrowed_book("b1")
        assert "b1" not in u.borrowed_books

    def test_borrow_count_increases(self):
        u = make_user()
        u.add_borrowed_book("b1")
        u.add_borrowed_book("b2")
        assert u.borrow_count == 2

    def test_add_reserved_book(self):
        u = make_user()
        u.add_reserved_book("b1")
        assert "b1" in u.reserved_books

    def test_remove_reserved_book(self):
        u = make_user()
        u.add_reserved_book("b1")
        u.remove_reserved_book("b1")
        assert "b1" not in u.reserved_books

    def test_repr_contains_name(self):
        u = make_user(name="Alice")
        assert "Alice" in repr(u)
