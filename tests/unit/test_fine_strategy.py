"""Unit tests for fine calculation strategies."""
import pytest
from src.services.fine_strategy import (
    StandardFineStrategy, ProgressiveFineStrategy,
    FlatFineStrategy, WeeklyFineStrategy, FineCalculator,
)
from tests.conftest import make_loan


def overdue(days):
    return make_loan(overdue_days=days)


def not_overdue():
    return make_loan(days_until_due=5)


class TestStandardFineStrategy:
    def test_name(self):
        s = StandardFineStrategy()
        assert s.name() == "standard"

    def test_no_fine_when_not_overdue(self):
        s = StandardFineStrategy()
        assert s.calculate(not_overdue()) == 0.0

    def test_fine_1_day(self):
        s = StandardFineStrategy()
        assert s.calculate(overdue(1)) == 0.50

    def test_fine_7_days(self):
        s = StandardFineStrategy()
        assert s.calculate(overdue(7)) == 3.50

    def test_fine_14_days(self):
        s = StandardFineStrategy()
        assert s.calculate(overdue(14)) == 7.00

    def test_fine_30_days(self):
        s = StandardFineStrategy()
        assert s.calculate(overdue(30)) == 15.00

    def test_fine_rounded_to_2_decimals(self):
        s = StandardFineStrategy()
        result = s.calculate(overdue(3))
        assert result == round(result, 2)


class TestProgressiveFineStrategy:
    def test_name(self):
        s = ProgressiveFineStrategy()
        assert s.name() == "progressive"

    def test_no_fine_not_overdue(self):
        s = ProgressiveFineStrategy()
        assert s.calculate(not_overdue()) == 0.0

    def test_first_week_base_rate(self):
        s = ProgressiveFineStrategy()
        # 7 days × 0.50 = 3.50
        assert s.calculate(overdue(7)) == 3.50

    def test_second_week_higher_rate(self):
        s = ProgressiveFineStrategy()
        # 7×0.50 + 7×1.00 = 3.50 + 7.00 = 10.50
        assert s.calculate(overdue(14)) == 10.50

    def test_after_14_days_highest_rate(self):
        s = ProgressiveFineStrategy()
        # 7×0.50 + 7×1.00 + 1×2.00 = 3.50 + 7.00 + 2.00 = 12.50
        assert s.calculate(overdue(15)) == 12.50

    def test_1_day_progressive(self):
        s = ProgressiveFineStrategy()
        assert s.calculate(overdue(1)) == 0.50

    def test_8_days_progressive(self):
        s = ProgressiveFineStrategy()
        # 7×0.50 + 1×1.00 = 4.50
        assert s.calculate(overdue(8)) == 4.50

    def test_progressive_more_than_standard_after_7_days(self):
        std = StandardFineStrategy()
        prog = ProgressiveFineStrategy()
        assert prog.calculate(overdue(14)) > std.calculate(overdue(14))


class TestFlatFineStrategy:
    def test_name(self):
        s = FlatFineStrategy()
        assert s.name() == "flat"

    def test_no_fine_not_overdue(self):
        s = FlatFineStrategy()
        assert s.calculate(not_overdue()) == 0.0

    def test_flat_amount_1_day(self):
        s = FlatFineStrategy()
        assert s.calculate(overdue(1)) == 5.00

    def test_flat_amount_30_days(self):
        s = FlatFineStrategy()
        assert s.calculate(overdue(30)) == 5.00

    def test_flat_amount_same_regardless_of_days(self):
        s = FlatFineStrategy()
        assert s.calculate(overdue(1)) == s.calculate(overdue(100))


class TestWeeklyFineStrategy:
    def test_name(self):
        s = WeeklyFineStrategy()
        assert s.name() == "weekly"

    def test_no_fine_not_overdue(self):
        s = WeeklyFineStrategy()
        assert s.calculate(not_overdue()) == 0.0

    def test_1_day_1_week(self):
        s = WeeklyFineStrategy()
        assert s.calculate(overdue(1)) == 3.00

    def test_7_days_1_week(self):
        s = WeeklyFineStrategy()
        assert s.calculate(overdue(7)) == 3.00

    def test_8_days_2_weeks(self):
        s = WeeklyFineStrategy()
        assert s.calculate(overdue(8)) == 6.00

    def test_14_days_2_weeks(self):
        s = WeeklyFineStrategy()
        assert s.calculate(overdue(14)) == 6.00

    def test_15_days_3_weeks(self):
        s = WeeklyFineStrategy()
        assert s.calculate(overdue(15)) == 9.00


class TestFineCalculator:
    def test_uses_injected_strategy(self):
        calc = FineCalculator(StandardFineStrategy())
        loan = overdue(2)
        assert calc.calculate_fine(loan) == 1.00

    def test_strategy_can_be_swapped(self):
        calc = FineCalculator(StandardFineStrategy())
        calc.set_strategy(FlatFineStrategy())
        assert calc.strategy_name() == "flat"

    def test_strategy_name(self):
        calc = FineCalculator(ProgressiveFineStrategy())
        assert calc.strategy_name() == "progressive"
