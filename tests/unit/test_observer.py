"""Unit tests for Observer pattern."""
import pytest
from unittest.mock import MagicMock

from src.services.observer import EventBus, LibraryEvent, NotificationObserver
from src.models.notification import NotificationType
from src.storage.in_memory import InMemoryNotificationRepository


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        observer = MagicMock()
        bus.subscribe("test_event", observer)
        event = LibraryEvent("test_event", {"key": "val"})
        bus.publish(event)
        observer.update.assert_called_once_with(event)

    def test_publish_no_observers_no_error(self):
        bus = EventBus()
        event = LibraryEvent("no_observers", {})
        bus.publish(event)  # should not raise

    def test_unsubscribe(self):
        bus = EventBus()
        observer = MagicMock()
        bus.subscribe("event", observer)
        bus.unsubscribe("event", observer)
        bus.publish(LibraryEvent("event", {}))
        observer.update.assert_not_called()

    def test_subscribe_all(self):
        bus = EventBus()
        observer = MagicMock()
        bus.subscribe_all(observer, ["e1", "e2"])
        bus.publish_event("e1", {})
        bus.publish_event("e2", {})
        assert observer.update.call_count == 2

    def test_publish_event_shortcut(self):
        bus = EventBus()
        observer = MagicMock()
        bus.subscribe("myevent", observer)
        bus.publish_event("myevent", {"a": 1})
        observer.update.assert_called_once()

    def test_same_observer_not_duplicated(self):
        bus = EventBus()
        observer = MagicMock()
        bus.subscribe("event", observer)
        bus.subscribe("event", observer)
        bus.publish_event("event", {})
        assert observer.update.call_count == 1

    def test_multiple_observers(self):
        bus = EventBus()
        o1 = MagicMock()
        o2 = MagicMock()
        bus.subscribe("event", o1)
        bus.subscribe("event", o2)
        bus.publish_event("event", {})
        o1.update.assert_called_once()
        o2.update.assert_called_once()


class TestNotificationObserver:
    def setup_method(self):
        self.repo = InMemoryNotificationRepository()
        self.observer = NotificationObserver(self.repo)

    def test_book_returned_creates_notification(self):
        event = LibraryEvent("book_returned", {"user_id": "u1", "book_title": "Test"})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert len(notifs) == 1
        assert notifs[0].type == NotificationType.BOOK_RETURNED

    def test_book_overdue_creates_notification(self):
        event = LibraryEvent("book_overdue", {"user_id": "u1", "book_title": "Test", "days": 5})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert notifs[0].type == NotificationType.OVERDUE_REMINDER

    def test_fine_charged_creates_notification(self):
        event = LibraryEvent("fine_charged", {"user_id": "u1", "amount": 5.0, "book_title": "Test"})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert notifs[0].type == NotificationType.FINE_CHARGED

    def test_user_blocked_creates_notification(self):
        event = LibraryEvent("user_blocked", {"user_id": "u1", "fine_amount": 50.0})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert notifs[0].type == NotificationType.ACCOUNT_BLOCKED

    def test_book_available_notifies_waiting_users(self):
        event = LibraryEvent("book_available", {"book_title": "Test", "waiting_users": ["u1", "u2"]})
        self.observer.update(event)
        assert len(self.repo.find_by_user("u1")) == 1
        assert len(self.repo.find_by_user("u2")) == 1

    def test_reservation_ready_notification(self):
        event = LibraryEvent("reservation_ready", {"user_id": "u1", "book_title": "Test"})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert notifs[0].type == NotificationType.RESERVATION_READY

    def test_loan_extended_notification(self):
        event = LibraryEvent("loan_extended", {"user_id": "u1", "book_title": "Test"})
        self.observer.update(event)
        notifs = self.repo.find_by_user("u1")
        assert notifs[0].type == NotificationType.LOAN_EXTENDED

    def test_unknown_event_no_error(self):
        event = LibraryEvent("unknown_event", {})
        self.observer.update(event)  # should not raise

    def test_notification_unread_by_default(self):
        event = LibraryEvent("book_returned", {"user_id": "u1", "book_title": "Test"})
        self.observer.update(event)
        notif = self.repo.find_by_user("u1")[0]
        assert notif.read is False
