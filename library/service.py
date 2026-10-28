"""Business rules: lending limits, due dates and overdue fines.

The clock is injected (`today`) so tests never depend on the real date.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, List

from .models import Book, LibraryError, Loan
from .repository import SqliteRepository

LOAN_DAYS = 14
MAX_ACTIVE_LOANS = 3
FINE_PER_DAY = 2  # rupees per day overdue


def fine_for(due: date, returned: date) -> int:
    return max(0, (returned - due).days) * FINE_PER_DAY


class LibraryService:
    def __init__(self, repo: SqliteRepository, today: Callable[[], date] = date.today) -> None:
        self._repo, self._today = repo, today

    def search(self, query: str) -> List[Book]:
        return self._repo.search_books(query.strip())

    def check_out(self, book_id: int, member_id: int) -> Loan:
        book, member = self._repo.get_book(book_id), self._repo.get_member(member_id)
        if book is None:
            raise LibraryError(f"No book with id {book_id}")
        if member is None:
            raise LibraryError(f"No member with id {member_id}")
        if book.available < 1:
            raise LibraryError(f"No copies of '{book.title}' are available")
        if self._repo.find_active_loan(book_id, member_id):
            raise LibraryError(f"{member.name} already has '{book.title}'")
        if len(self._repo.active_loans(member_id)) >= MAX_ACTIVE_LOANS:
            raise LibraryError(f"{member.name} has reached the {MAX_ACTIVE_LOANS}-book limit")
        today = self._today()
        return self._repo.create_loan(book_id, member_id, today, today + timedelta(days=LOAN_DAYS))

    def check_in(self, book_id: int, member_id: int) -> Loan:
        loan = self._repo.find_active_loan(book_id, member_id)
        if loan is None:
            raise LibraryError("That member does not have this book checked out")
        today = self._today()
        return self._repo.close_loan(loan.id, today, fine_for(loan.due, today))

    def overdue(self) -> List[Loan]:
        return self._repo.overdue_loans(self._today())
