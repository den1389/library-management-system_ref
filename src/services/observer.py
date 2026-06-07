"""Observer Pattern — notification events system."""
from abc import ABC, abstractmethod
from typing import Dict, List
import uuid
from datetime import datetime

from src.models.notification import Notification, NotificationType
from src.storage.interfaces import NotificationRepository


class LibraryEvent:
    """Base library event."""
    def __init__(self, event_type: str, payload: dict):
        self.event_type = event_type
        self.payload = payload
        self.occurred_at = datetime.now()


class EventObserver(ABC):
    """Abstract observer interface."""

    @abstractmethod
    def update(self, event: LibraryEvent) -> None:
        pass


class NotificationObserver(EventObserver):
    """Observer that creates notifications in repository."""

    def __init__(self, notification_repo: NotificationRepository):
        self._repo = notification_repo

    def update(self, event: LibraryEvent) -> None:
        handlers = {
            "book_returned": self._on_book_returned,
            "book_overdue": self._on_book_overdue,
            "fine_charged": self._on_fine_charged,
            "user_blocked": self._on_user_blocked,
            "book_available": self._on_book_available,
            "reservation_ready": self._on_reservation_ready,
            "loan_extended": self._on_loan_extended,
        }
        handler = handlers.get(event.event_type)
        if handler:
            handler(event.payload)

    def _create(self, user_id: str, ntype: NotificationType, message: str) -> None:
        n = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=ntype,
            message=message,
        )
        self._repo.save(n)

    def _on_book_returned(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.BOOK_RETURNED,
                     f"Книгу '{p['book_title']}' повернуто успішно.")

    def _on_book_overdue(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.OVERDUE_REMINDER,
                     f"Книга '{p['book_title']}' прострочена на {p['days']} днів!")

    def _on_fine_charged(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.FINE_CHARGED,
                     f"Нараховано штраф {p['amount']} грн за книгу '{p['book_title']}'.")

    def _on_user_blocked(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.ACCOUNT_BLOCKED,
                     f"Ваш акаунт заблоковано. Сума штрафів: {p['fine_amount']} грн.")

    def _on_book_available(self, p: dict) -> None:
        for uid in p.get("waiting_users", []):
            self._create(uid, NotificationType.BOOK_AVAILABLE,
                         f"Книга '{p['book_title']}' тепер доступна для резервування.")

    def _on_reservation_ready(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.RESERVATION_READY,
                     f"Ваше резервування книги '{p['book_title']}' підтверджено.")

    def _on_loan_extended(self, p: dict) -> None:
        self._create(p["user_id"], NotificationType.LOAN_EXTENDED,
                     f"Термін повернення книги '{p['book_title']}' продовжено на 7 днів.")


class EventBus:
    """Central event bus — subject in Observer pattern."""

    def __init__(self):
        self._observers: Dict[str, List[EventObserver]] = {}

    def subscribe(self, event_type: str, observer: EventObserver) -> None:
        if event_type not in self._observers:
            self._observers[event_type] = []
        if observer not in self._observers[event_type]:
            self._observers[event_type].append(observer)

    def subscribe_all(self, observer: EventObserver, event_types: List[str]) -> None:
        for et in event_types:
            self.subscribe(et, observer)

    def unsubscribe(self, event_type: str, observer: EventObserver) -> None:
        if event_type in self._observers:
            self._observers[event_type] = [
                o for o in self._observers[event_type] if o is not observer
            ]

    def publish(self, event: LibraryEvent) -> None:
        for observer in self._observers.get(event.event_type, []):
            observer.update(event)

    def publish_event(self, event_type: str, payload: dict) -> None:
        self.publish(LibraryEvent(event_type, payload))
