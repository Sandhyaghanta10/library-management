"""Sample data for demos and screenshots (all names are fictional).

Loans use historical dates (2018-2023) so the Overdue tab and the fine calculation have something to show.
"""
from __future__ import annotations

from datetime import date, timedelta

from .repository import SqliteRepository
from .service import LOAN_DAYS, fine_for

_BOOKS = [  # (title, author, copies)
    ("Operating Systems: Three Easy Pieces", "Remzi & Andrea Arpaci-Dusseau", 2),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", 2),
    ("Introduction to Algorithms", "Cormen, Leiserson, Rivest, Stein", 1),
    ("Database Internals", "Alex Petrov", 1),
    ("Clean Code", "Robert C. Martin", 2),
    ("The Pragmatic Programmer", "Hunt & Thomas", 1),
]
_MEMBERS = [("Asha Reddy", "asha@example.com"), ("Ravi Kumar", "ravi@example.com"),
            ("Meena Iyer", "meena@example.com"), ("Karthik Subramanian", "karthik@example.com")]
# (book index, member index, checked out, returned or None = still out)
_LOANS = [
    (0, 0, date(2018, 11, 8), date(2018, 12, 1)),   # 9 days late -> fine
    (1, 0, date(2022, 3, 1), date(2022, 3, 10)),    # on time
    (2, 1, date(2022, 3, 5), date(2022, 4, 2)),     # 14 days late -> fine
    (4, 2, date(2023, 11, 20), None),               # still out -> overdue
    (3, 3, date(2023, 12, 1), None),                # still out -> overdue
]


def seed_demo(repo: SqliteRepository) -> bool:
    """Load sample data into an empty library. Returns False (and does nothing) if books already exist."""
    if repo.search_books(""):
        return False
    books = [repo.add_book(title, author, f"DEMO-{i + 1:04d}", copies)
             for i, (title, author, copies) in enumerate(_BOOKS)]
    members = [repo.add_member(name, email) for name, email in _MEMBERS]
    for book_i, member_i, out, returned in _LOANS:
        due = out + timedelta(days=LOAN_DAYS)
        loan = repo.create_loan(books[book_i].id, members[member_i].id, out, due)
        if returned:
            repo.close_loan(loan.id, returned, fine_for(due, returned))
    return True
