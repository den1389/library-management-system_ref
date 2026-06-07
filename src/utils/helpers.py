"""Utility helpers."""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


def generate_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now()


def future_date(days: int) -> datetime:
    return datetime.now() + timedelta(days=days)


def past_date(days: int) -> datetime:
    return datetime.now() - timedelta(days=days)


def format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def days_between(start: datetime, end: datetime) -> int:
    return (end - start).days


def build_stats_report(stats: Dict[str, Any]) -> str:
    lines = ["=== Статистика бібліотеки ==="]
    for key, val in stats.items():
        lines.append(f"  {key}: {val}")
    return "\n".join(lines)
