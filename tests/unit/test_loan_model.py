"""Unit tests for Loan model."""
import pytest
from datetime import datetime, timedelta

from src.models.loan import Loan, LoanStatus
from tests.conftest import make_loan


class TestLoanCreation:
    def test_default_status_active(self):
        l = make_loan()
        assert l.status == LoanStatus.ACTIVE

    def test_default_fine_zero(self):
        l = make_loan()
        assert l.fine_amount == 0.0

    def test_extended_false_by_default(self):
        l = make_loan()
        assert l.extended is False

    def test_returned_at_none(self):
        l = make_loan()
        assert l.returned_at is None

    def test_loan_fields_set(self):
        l = make_loan(loan_id="l99", book_id="b99", user_id="u99")
        assert l.id == "l99"
        assert l.book_id == "b99"
        assert l.user_id == "u99"


class TestLoanOverdue:
    def test_not_overdue_when_future_due(self):
        l = make_loan(days_until_due=5)
        assert l.is_overdue() is False

    def test_overdue_when_past_due(self):
        l = make_loan(overdue_days=3)
        assert l.is_overdue() is True

    def test_days_overdue_zero_when_not_overdue(self):
        l = make_loan(days_until_due=5)
        assert l.days_overdue() == 0

    def test_days_overdue_correct(self):
        l = make_loan(overdue_days=5)
        assert l.days_overdue() >= 5

    def test_returned_loan_not_overdue(self):
        l = make_loan(overdue_days=3)
        l.status = LoanStatus.RETURNED
        assert l.is_overdue() is False

    def test_days_remaining_positive_when_not_due(self):
        l = make_loan(days_until_due=7)
        assert l.days_remaining() >= 6

    def test_days_remaining_zero_for_returned(self):
        l = make_loan()
        l.status = LoanStatus.RETURNED
        assert l.days_remaining() == 0


class TestLoanExtension:
    def test_can_extend_active_not_overdue(self):
        l = make_loan(days_until_due=5)
        assert l.can_extend() is True

    def test_cannot_extend_if_already_extended(self):
        l = make_loan(days_until_due=5)
        l.extended = True
        assert l.can_extend() is False

    def test_cannot_extend_if_overdue(self):
        l = make_loan(overdue_days=2)
        assert l.can_extend() is False

    def test_extend_adds_7_days(self):
        l = make_loan(days_until_due=5)
        original_due = l.due_date
        l.extend()
        assert l.due_date == original_due + timedelta(days=7)

    def test_extend_marks_extended_true(self):
        l = make_loan(days_until_due=5)
        l.extend()
        assert l.extended is True

    def test_extend_returned_loan_not_extended(self):
        l = make_loan()
        l.status = LoanStatus.RETURNED
        l.extend()  # should not change
        assert l.extended is False


class TestLoanStatusChanges:
    def test_mark_returned_sets_status(self):
        l = make_loan()
        l.mark_returned()
        assert l.status == LoanStatus.RETURNED

    def test_mark_returned_sets_returned_at(self):
        l = make_loan()
        l.mark_returned()
        assert l.returned_at is not None

    def test_mark_returned_custom_date(self):
        l = make_loan()
        dt = datetime(2024, 1, 15)
        l.mark_returned(dt)
        assert l.returned_at == dt

    def test_mark_lost(self):
        l = make_loan()
        l.mark_lost()
        assert l.status == LoanStatus.LOST

    def test_update_status_marks_overdue(self):
        l = make_loan(overdue_days=3)
        l.update_status()
        assert l.status == LoanStatus.OVERDUE

    def test_update_status_no_change_when_not_overdue(self):
        l = make_loan(days_until_due=5)
        l.update_status()
        assert l.status == LoanStatus.ACTIVE

    def test_repr_contains_status(self):
        l = make_loan()
        assert "active" in repr(l)
