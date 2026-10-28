from datetime import date

from library.demo import seed_demo
from library.repository import SqliteRepository
from library.service import FINE_PER_DAY, LibraryService

# Ravi: due 2022-03-19, returned 2022-04-02 -> 14 days late. Asha: due 2018-11-22, returned 2018-12-01 -> 9 days late.


def test_seed_loads_once_and_is_idempotent():
    repo = SqliteRepository()
    assert seed_demo(repo) is True
    assert seed_demo(repo) is False
    assert len(repo.search_books("")) == 6


def test_demo_fines_and_overdue_use_historical_dates():
    repo = SqliteRepository()
    seed_demo(repo)
    assert repo.total_fines(1) == 9 * FINE_PER_DAY    # Asha (member 1)
    assert repo.total_fines(2) == 14 * FINE_PER_DAY   # Ravi (member 2)
    service = LibraryService(repo, today=lambda: date(2023, 12, 31))
    assert sorted(loan.member_id for loan in service.overdue()) == [3, 4]


def test_demo_availability_reflects_open_loans():
    repo = SqliteRepository()
    seed_demo(repo)
    by_title = {b.title: b for b in repo.search_books("")}
    assert by_title["Database Internals"].available == 0   # 1 copy, out on loan
    assert by_title["Clean Code"].available == 1           # 2 copies, 1 out
    assert by_title["Introduction to Algorithms"].available == 1  # returned
