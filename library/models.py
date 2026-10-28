"""Plain data objects shared by the repository, service and GUI layers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str
    isbn: str
    copies: int
    available: int


@dataclass(frozen=True)
class Member:
    id: int
    name: str
    email: str


@dataclass(frozen=True)
class Loan:
    id: int
    book_id: int
    member_id: int
    checked_out: date
    due: date
    returned: Optional[date] = None
    fine: int = 0  # whole rupees, set when the book comes back


class LibraryError(Exception):
    """A business-rule violation (no copies left, loan limit hit, ...)."""
