"""Fine calculation strategies — GoF Strategy Pattern."""
from abc import ABC, abstractmethod
from datetime import datetime

from src.models.loan import Loan


class FineStrategy(ABC):
    """Abstract fine calculation strategy."""

    @abstractmethod
    def calculate(self, loan: Loan) -> float:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class StandardFineStrategy(FineStrategy):
    """Standard fine: 0.50 UAH per day overdue."""

    DAILY_RATE = 0.50

    def calculate(self, loan: Loan) -> float:
        days = loan.days_overdue()
        return round(days * self.DAILY_RATE, 2)

    def name(self) -> str:
        return "standard"


class ProgressiveFineStrategy(FineStrategy):
    """Progressive fine: increases after 7 and 14 days."""

    BASE_RATE = 0.50
    WEEK_RATE = 1.00
    FORTNIGHT_RATE = 2.00

    def calculate(self, loan: Loan) -> float:
        days = loan.days_overdue()
        if days <= 0:
            return 0.0
        fine = 0.0
        first_week = min(days, 7)
        fine += first_week * self.BASE_RATE
        second_week = min(max(days - 7, 0), 7)
        fine += second_week * self.WEEK_RATE
        remaining = max(days - 14, 0)
        fine += remaining * self.FORTNIGHT_RATE
        return round(fine, 2)

    def name(self) -> str:
        return "progressive"


class FlatFineStrategy(FineStrategy):
    """Flat fine regardless of days overdue."""

    FLAT_AMOUNT = 5.00

    def calculate(self, loan: Loan) -> float:
        return self.FLAT_AMOUNT if loan.days_overdue() > 0 else 0.0

    def name(self) -> str:
        return "flat"


class WeeklyFineStrategy(FineStrategy):
    """Fine charged per started week overdue."""

    WEEKLY_RATE = 3.00

    def calculate(self, loan: Loan) -> float:
        days = loan.days_overdue()
        if days <= 0:
            return 0.0
        import math
        weeks = math.ceil(days / 7)
        return round(weeks * self.WEEKLY_RATE, 2)

    def name(self) -> str:
        return "weekly"


class FineCalculator:
    """Context for fine strategy — uses injected strategy."""

    def __init__(self, strategy: FineStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: FineStrategy) -> None:
        self._strategy = strategy

    def calculate_fine(self, loan: Loan) -> float:
        return self._strategy.calculate(loan)

    def strategy_name(self) -> str:
        return self._strategy.name()
