"""Unit tests for Book model."""
import pytest
from datetime import datetime, timedelta

from src.models.book import Book, BookStatus
from tests.conftest import make_book


class TestBookCreation:
    def test_book_default_status_available(self):
        b = make_book()
        assert b.status == BookStatus.AVAILABLE

    def test_book_fields_set_correctly(self):
        b = make_book(book_id="x", title="T", author="A", isbn="999", year=2021, genre="Sci-Fi")
        assert b.id == "x"
        assert b.title == "T"
        assert b.author == "A"
        assert b.isbn == "999"
        assert b.year == 2021
        assert b.genre == "Sci-Fi"

    def test_book_reservation_queue_empty_by_default(self):
        b = make_book()
        assert b.reservation_queue == []

    def test_book_borrower_none_by_default(self):
        b = make_book()
        assert b.borrower_id is None

    def test_book_due_date_none_by_default(self):
        b = make_book()
        assert b.due_date is None


class TestBookStatusChecks:
    def test_is_available_true(self):
        b = make_book(status=BookStatus.AVAILABLE)
        assert b.is_available() is True

    def test_is_available_false_when_borrowed(self):
        b = make_book(status=BookStatus.BORROWED)
        assert b.is_available() is False

    def test_is_borrowed_true(self):
        b = make_book(status=BookStatus.BORROWED)
        assert b.is_borrowed() is True

    def test_is_borrowed_false_when_available(self):
        b = make_book()
        assert b.is_borrowed() is False

    def test_is_reserved_true(self):
        b = make_book(status=BookStatus.RESERVED)
        assert b.is_reserved() is True

    def test_is_reserved_false_when_available(self):
        b = make_book()
        assert b.is_reserved() is False

    def test_book_lost_status(self):
        b = make_book(status=BookStatus.LOST)
        assert b.status == BookStatus.LOST
        assert not b.is_available()
        assert not b.is_borrowed()


class TestBookQueue:
    def test_add_to_queue(self):
        b = make_book()
        b.add_to_queue("u1")
        assert "u1" in b.reservation_queue

    def test_add_same_user_twice_no_duplicate(self):
        b = make_book()
        b.add_to_queue("u1")
        b.add_to_queue("u1")
        assert b.reservation_queue.count("u1") == 1

    def test_add_multiple_users(self):
        b = make_book()
        b.add_to_queue("u1")
        b.add_to_queue("u2")
        b.add_to_queue("u3")
        assert len(b.reservation_queue) == 3

    def test_queue_order_preserved(self):
        b = make_book()
        b.add_to_queue("u1")
        b.add_to_queue("u2")
        assert b.reservation_queue[0] == "u1"
        assert b.reservation_queue[1] == "u2"

    def test_remove_from_queue(self):
        b = make_book()
        b.add_to_queue("u1")
        b.remove_from_queue("u1")
        assert "u1" not in b.reservation_queue

    def test_remove_nonexistent_from_queue_no_error(self):
        b = make_book()
        b.remove_from_queue("u999")  # should not raise

    def test_has_reservation_queue_false_when_empty(self):
        b = make_book()
        assert b.has_reservation_queue() is False

    def test_has_reservation_queue_true_when_users(self):
        b = make_book()
        b.add_to_queue("u1")
        assert b.has_reservation_queue() is True

    def test_next_in_queue_returns_first(self):
        b = make_book()
        b.add_to_queue("u1")
        b.add_to_queue("u2")
        assert b.next_in_queue() == "u1"

    def test_next_in_queue_none_when_empty(self):
        b = make_book()
        assert b.next_in_queue() is None

    def test_remove_first_shifts_queue(self):
        b = make_book()
        b.add_to_queue("u1")
        b.add_to_queue("u2")
        b.remove_from_queue("u1")
        assert b.next_in_queue() == "u2"


class TestBookStatuses:
    def test_status_change_from_available_to_borrowed(self):
        b = make_book()
        b.status = BookStatus.BORROWED
        assert b.is_borrowed()

    def test_status_change_from_borrowed_to_available(self):
        b = make_book(status=BookStatus.BORROWED)
        b.status = BookStatus.AVAILABLE
        assert b.is_available()

    def test_book_repr(self):
        b = make_book(book_id="x", title="Test")
        r = repr(b)
        assert "x" in r
        assert "Test" in r

    def test_book_status_all_values(self):
        for s in BookStatus:
            b = make_book(status=s)
            assert b.status == s
