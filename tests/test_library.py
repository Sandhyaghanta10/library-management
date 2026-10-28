from datetime import date, timedelta

import pytest

from library.models import LibraryError
from library.repository import SqliteRepository
from library.service import FINE_PER_DAY, LOAN_DAYS, MAX_ACTIVE_LOANS, LibraryService, fine_for

START = date(2026, 1, 1)


class Clock:
    """Controllable clock so we can time-travel past due dates."""
    def __init__(self):
        self.now = START

    def __call__(self):
        return self.now

    def advance(self, days):
        self.now += timedelta(days=days)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def repo():
    return SqliteRepository()


@pytest.fixture
def service(repo, clock):
    return LibraryService(repo, clock)


@pytest.fixture
def member(repo):
    return repo.add_member("Asha", "asha@example.com")


def add_book(repo, n=1, copies=1):
    return repo.add_book(f"Book {n}", f"Author {n}", f"isbn-{n}", copies)


def test_search_matches_title_author_and_isbn(repo, service):
    repo.add_book("Operating Systems: Three Easy Pieces", "Arpaci-Dusseau", "111", 1)
    repo.add_book("Database Internals", "Petrov", "222", 1)
    assert [b.isbn for b in service.search("three easy")] == ["111"]
    assert [b.isbn for b in service.search("petrov")] == ["222"]
    assert [b.isbn for b in service.search("222")] == ["222"]
    assert service.search("zzz") == []


def test_checkout_sets_due_date_and_reduces_availability(repo, service, member):
    book = add_book(repo, copies=2)
    loan = service.check_out(book.id, member.id)
    assert loan.due == START + timedelta(days=LOAN_DAYS)
    assert repo.get_book(book.id).available == 1


def test_cannot_checkout_when_no_copies_left(repo, service, member):
    book = add_book(repo, copies=1)
    other = repo.add_member("Ravi", "ravi@example.com")
    service.check_out(book.id, member.id)
    with pytest.raises(LibraryError, match="No copies"):
        service.check_out(book.id, other.id)


def test_cannot_borrow_same_book_twice(repo, service, member):
    book = add_book(repo, copies=2)
    service.check_out(book.id, member.id)
    with pytest.raises(LibraryError, match="already has"):
        service.check_out(book.id, member.id)


def test_loan_limit(repo, service, member):
    books = [add_book(repo, n) for n in range(MAX_ACTIVE_LOANS + 1)]
    for book in books[:MAX_ACTIVE_LOANS]:
        service.check_out(book.id, member.id)
    with pytest.raises(LibraryError, match="limit"):
        service.check_out(books[-1].id, member.id)


def test_unknown_book_or_member(service, member, repo):
    with pytest.raises(LibraryError, match="No book"):
        service.check_out(999, member.id)
    with pytest.raises(LibraryError, match="No member"):
        service.check_out(add_book(repo).id, 999)


def test_on_time_return_has_no_fine_and_frees_the_copy(repo, service, clock, member):
    book = add_book(repo)
    service.check_out(book.id, member.id)
    clock.advance(LOAN_DAYS)  # returned exactly on the due date
    loan = service.check_in(book.id, member.id)
    assert loan.fine == 0 and loan.returned == clock.now
    assert repo.get_book(book.id).available == 1


def test_late_return_is_fined_per_day(repo, service, clock, member):
    book = add_book(repo)
    service.check_out(book.id, member.id)
    clock.advance(LOAN_DAYS + 5)
    assert service.check_in(book.id, member.id).fine == 5 * FINE_PER_DAY
    assert repo.total_fines(member.id) == 5 * FINE_PER_DAY


def test_check_in_without_loan_fails(repo, service, member):
    with pytest.raises(LibraryError):
        service.check_in(add_book(repo).id, member.id)


def test_overdue_list(repo, service, clock, member):
    book = add_book(repo)
    service.check_out(book.id, member.id)
    clock.advance(LOAN_DAYS)
    assert service.overdue() == []
    clock.advance(1)
    assert [l.book_id for l in service.overdue()] == [book.id]


def test_fine_never_negative():
    assert fine_for(date(2026, 1, 10), date(2026, 1, 1)) == 0
