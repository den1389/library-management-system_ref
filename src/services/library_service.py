"""Core Library Service — orchestrates all business operations."""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from src.models.book import Book, BookStatus
from src.models.loan import Loan, LoanStatus
from src.models.user import User, UserRole, UserStatus
from src.services.fine_strategy import FineCalculator, StandardFineStrategy, FineStrategy
from src.services.observer import EventBus, NotificationObserver
from src.storage.interfaces import BookRepository, LoanRepository, NotificationRepository, UserRepository


class LibraryException(Exception):
    pass


class BookNotAvailableError(LibraryException):
    pass


class UserBlockedError(LibraryException):
    pass


class BorrowLimitExceededError(LibraryException):
    pass


class BookNotFoundError(LibraryException):
    pass


class UserNotFoundError(LibraryException):
    pass


class LoanNotFoundError(LibraryException):
    pass


class AlreadyBorrowedError(LibraryException):
    pass


class LibraryService:
    """Main library service — Single Responsibility per method, DI via constructor."""

    def __init__(
        self,
        book_repo: BookRepository,
        user_repo: UserRepository,
        loan_repo: LoanRepository,
        notification_repo: NotificationRepository,
        fine_strategy: Optional[FineStrategy] = None,
    ):
        self._books = book_repo
        self._users = user_repo
        self._loans = loan_repo
        self._notifications = notification_repo
        self._fine_calc = FineCalculator(fine_strategy or StandardFineStrategy())
        self._event_bus = EventBus()
        observer = NotificationObserver(notification_repo)
        all_events = [
            "book_returned", "book_overdue", "fine_charged",
            "user_blocked", "book_available", "reservation_ready", "loan_extended",
        ]
        self._event_bus.subscribe_all(observer, all_events)

    # ── Book management ──────────────────────────────────────────────────────

    def add_book(self, title: str, author: str, isbn: str, year: int, genre: str) -> Book:
        if self._books.find_by_isbn(isbn):
            raise LibraryException(f"Книга з ISBN {isbn} вже існує.")
        book = Book(id=str(uuid.uuid4()), title=title, author=author,
                    isbn=isbn, year=year, genre=genre)
        return self._books.save(book)

    def get_book(self, book_id: str) -> Book:
        book = self._books.find_by_id(book_id)
        if not book:
            raise BookNotFoundError(f"Книгу {book_id} не знайдено.")
        return book

    def remove_book(self, book_id: str) -> bool:
        book = self.get_book(book_id)
        if book.is_borrowed():
            raise LibraryException("Неможливо видалити позичену книгу.")
        return self._books.delete(book_id)

    def search_books(self, query: str) -> List[Book]:
        return self._books.search(query)

    def list_available_books(self) -> List[Book]:
        return self._books.find_available()

    def list_all_books(self) -> List[Book]:
        return self._books.find_all()

    # ── User management ──────────────────────────────────────────────────────

    def register_user(self, name: str, email: str, role: UserRole = UserRole.READER) -> User:
        if self._users.find_by_email(email):
            raise LibraryException(f"Користувач з email {email} вже зареєстрований.")
        user = User(id=str(uuid.uuid4()), name=name, email=email, role=role)
        return self._users.save(user)

    def get_user(self, user_id: str) -> User:
        user = self._users.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"Користувача {user_id} не знайдено.")
        return user

    def block_user(self, user_id: str) -> User:
        user = self.get_user(user_id)
        user.block()
        self._users.save(user)
        self._event_bus.publish_event("user_blocked", {
            "user_id": user.id, "fine_amount": user.fine_amount
        })
        return user

    def unblock_user(self, user_id: str) -> User:
        user = self.get_user(user_id)
        user.unblock()
        return self._users.save(user)

    def pay_fine(self, user_id: str, amount: float) -> float:
        user = self.get_user(user_id)
        paid = user.pay_fine(amount)
        self._users.save(user)
        return paid

    # ── Borrowing ────────────────────────────────────────────────────────────

    def borrow_book(self, user_id: str, book_id: str, days: int = 14) -> Loan:
        user = self.get_user(user_id)
        book = self.get_book(book_id)

        if user.is_blocked():
            raise UserBlockedError(f"Користувач {user.name} заблокований.")
        if not user.can_borrow():
            raise BorrowLimitExceededError("Перевищено ліміт позичань або є несплачені штрафи.")
        if not book.is_available():
            raise BookNotAvailableError(f"Книга '{book.title}' недоступна.")
        if self._loans.find_active_by_user_and_book(user_id, book_id):
            raise AlreadyBorrowedError("Ця книга вже позичена цим користувачем.")

        loan = Loan(
            id=str(uuid.uuid4()),
            book_id=book_id,
            user_id=user_id,
            due_date=datetime.now() + timedelta(days=days),
        )
        book.status = BookStatus.BORROWED
        book.borrower_id = user_id
        book.due_date = loan.due_date
        book.remove_from_queue(user_id)

        user.add_borrowed_book(book_id)
        user.remove_reserved_book(book_id)

        self._books.save(book)
        self._users.save(user)
        self._loans.save(loan)
        return loan

    def return_book(self, user_id: str, book_id: str) -> Loan:
        user = self.get_user(user_id)
        book = self.get_book(book_id)
        loan = self._loans.find_active_by_user_and_book(user_id, book_id)
        if not loan:
            raise LoanNotFoundError("Активної видачі не знайдено.")

        loan.update_status()
        fine = self._fine_calc.calculate_fine(loan)
        loan.mark_returned()

        if fine > 0:
            user.add_fine(fine)
            self._event_bus.publish_event("fine_charged", {
                "user_id": user.id, "amount": fine, "book_title": book.title
            })
            if user.is_blocked():
                self._event_bus.publish_event("user_blocked", {
                    "user_id": user.id, "fine_amount": user.fine_amount
                })

        user.remove_borrowed_book(book_id)
        next_user_id = book.next_in_queue()

        book.status = BookStatus.AVAILABLE if not next_user_id else BookStatus.RESERVED
        book.borrower_id = None
        book.due_date = None

        self._event_bus.publish_event("book_returned", {
            "user_id": user_id, "book_title": book.title
        })

        if next_user_id:
            self._event_bus.publish_event("reservation_ready", {
                "user_id": next_user_id, "book_title": book.title
            })
        else:
            self._event_bus.publish_event("book_available", {
                "book_title": book.title, "waiting_users": []
            })

        self._books.save(book)
        self._users.save(user)
        self._loans.save(loan)
        return loan

    def extend_loan(self, user_id: str, book_id: str) -> Loan:
        loan = self._loans.find_active_by_user_and_book(user_id, book_id)
        if not loan:
            raise LoanNotFoundError("Активної видачі не знайдено.")
        if not loan.can_extend():
            raise LibraryException("Продовження неможливе (вже продовжено або прострочено).")
        loan.extend()
        self._loans.save(loan)
        book = self.get_book(book_id)
        self._event_bus.publish_event("loan_extended", {
            "user_id": user_id, "book_title": book.title
        })
        return loan

    # ── Reservations ─────────────────────────────────────────────────────────

    def reserve_book(self, user_id: str, book_id: str) -> Book:
        user = self.get_user(user_id)
        book = self.get_book(book_id)
        if user.is_blocked():
            raise UserBlockedError("Заблокований користувач не може резервувати книги.")
        if book.is_available():
            raise LibraryException("Книга доступна — можна одразу позичити.")
        if user_id in book.reservation_queue:
            raise LibraryException("Ви вже в черзі на цю книгу.")
        book.add_to_queue(user_id)
        user.add_reserved_book(book_id)
        self._books.save(book)
        self._users.save(user)
        return book

    def cancel_reservation(self, user_id: str, book_id: str) -> Book:
        user = self.get_user(user_id)
        book = self.get_book(book_id)
        book.remove_from_queue(user_id)
        user.remove_reserved_book(book_id)
        if not book.has_reservation_queue() and book.status == BookStatus.RESERVED:
            book.status = BookStatus.AVAILABLE
        self._books.save(book)
        self._users.save(user)
        return book

    # ── Overdue processing ───────────────────────────────────────────────────

    def process_overdue_loans(self) -> List[Loan]:
        overdue = self._loans.find_overdue()
        processed = []
        for loan in overdue:
            loan.update_status()
            book = self._books.find_by_id(loan.book_id)
            if book:
                self._event_bus.publish_event("book_overdue", {
                    "user_id": loan.user_id,
                    "book_title": book.title,
                    "days": loan.days_overdue(),
                })
            self._loans.save(loan)
            processed.append(loan)
        return processed

    # ── Reports ──────────────────────────────────────────────────────────────

    def get_active_loans(self) -> List[Loan]:
        return self._loans.find_active()

    def get_overdue_loans(self) -> List[Loan]:
        return self._loans.find_overdue()

    def get_user_loans(self, user_id: str) -> List[Loan]:
        return self._loans.find_by_user(user_id)

    def get_statistics(self) -> dict:
        all_loans = self._loans.find_all()
        returned = [l for l in all_loans if l.status == LoanStatus.RETURNED]
        active = self._loans.find_active()
        overdue = self._loans.find_overdue()
        blocked_users = self._users.find_blocked()
        return {
            "total_books": len(self._books.find_all()),
            "available_books": len(self._books.find_available()),
            "total_users": len(self._users.find_all()),
            "blocked_users": len(blocked_users),
            "active_loans": len(active),
            "overdue_loans": len(overdue),
            "total_loans_ever": len(all_loans),
            "returned_loans": len(returned),
        }

    def set_fine_strategy(self, strategy: FineStrategy) -> None:
        self._fine_calc.set_strategy(strategy)
