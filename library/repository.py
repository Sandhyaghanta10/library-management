"""SQLite persistence. Only SQL lives here; business rules live in the service."""
from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional

from .models import Book, Loan, Member

_SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL,
    isbn TEXT NOT NULL UNIQUE, copies INTEGER NOT NULL CHECK (copies >= 0));
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    checked_out TEXT NOT NULL, due TEXT NOT NULL,
    returned TEXT, fine INTEGER NOT NULL DEFAULT 0);
"""

# `available` = copies minus loans that haven't come back yet.
_BOOK_SELECT = """
SELECT b.id, b.title, b.author, b.isbn, b.copies,
       b.copies - (SELECT COUNT(*) FROM loans l
                   WHERE l.book_id = b.id AND l.returned IS NULL) AS available
FROM books b
"""


def _loan(row: sqlite3.Row) -> Loan:
    return Loan(row["id"], row["book_id"], row["member_id"],
                date.fromisoformat(row["checked_out"]), date.fromisoformat(row["due"]),
                date.fromisoformat(row["returned"]) if row["returned"] else None,
                row["fine"])


class SqliteRepository:
    def __init__(self, path: str = ":memory:") -> None:
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db.executescript(_SCHEMA)

    # --- books & members ---------------------------------------------------
    def add_book(self, title: str, author: str, isbn: str, copies: int) -> Book:
        with self._db:
            cur = self._db.execute(
                "INSERT INTO books (title, author, isbn, copies) VALUES (?, ?, ?, ?)",
                (title, author, isbn, copies))
        return self.get_book(cur.lastrowid)

    def get_book(self, book_id: int) -> Optional[Book]:
        row = self._db.execute(_BOOK_SELECT + " WHERE b.id = ?", (book_id,)).fetchone()
        return Book(*row) if row else None

    def search_books(self, query: str) -> List[Book]:
        like = f"%{query}%"
        rows = self._db.execute(
            _BOOK_SELECT + " WHERE b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?"
            " ORDER BY b.title", (like, like, like)).fetchall()
        return [Book(*row) for row in rows]

    def add_member(self, name: str, email: str) -> Member:
        with self._db:
            cur = self._db.execute(
                "INSERT INTO members (name, email) VALUES (?, ?)", (name, email))
        return self.get_member(cur.lastrowid)

    def get_member(self, member_id: int) -> Optional[Member]:
        row = self._db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
        return Member(row["id"], row["name"], row["email"]) if row else None

    # --- loans -------------------------------------------------------------
    def create_loan(self, book_id: int, member_id: int, out: date, due: date) -> Loan:
        with self._db:
            cur = self._db.execute(
                "INSERT INTO loans (book_id, member_id, checked_out, due) VALUES (?, ?, ?, ?)",
                (book_id, member_id, out.isoformat(), due.isoformat()))
        return self._get_loan(cur.lastrowid)

    def _get_loan(self, loan_id: int) -> Loan:
        return _loan(self._db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone())

    def active_loans(self, member_id: int) -> List[Loan]:
        rows = self._db.execute(
            "SELECT * FROM loans WHERE member_id = ? AND returned IS NULL", (member_id,))
        return [_loan(r) for r in rows]

    def find_active_loan(self, book_id: int, member_id: int) -> Optional[Loan]:
        row = self._db.execute(
            "SELECT * FROM loans WHERE book_id = ? AND member_id = ? AND returned IS NULL",
            (book_id, member_id)).fetchone()
        return _loan(row) if row else None

    def close_loan(self, loan_id: int, returned: date, fine: int) -> Loan:
        with self._db:
            self._db.execute("UPDATE loans SET returned = ?, fine = ? WHERE id = ?",
                             (returned.isoformat(), fine, loan_id))
        return self._get_loan(loan_id)

    def overdue_loans(self, today: date) -> List[Loan]:
        rows = self._db.execute(
            "SELECT * FROM loans WHERE returned IS NULL AND due < ? ORDER BY due",
            (today.isoformat(),))
        return [_loan(r) for r in rows]

    def total_fines(self, member_id: int) -> int:
        (total,) = self._db.execute(
            "SELECT COALESCE(SUM(fine), 0) FROM loans WHERE member_id = ?",
            (member_id,)).fetchone()
        return total
