# Library Management System

Desktop app to manage library books, members, loans and overdue fines.

> Recreated in 2026. Originally built 2018–22.

## Features
- Add books (multiple copies) and members
- Search by title, author or ISBN
- Check-out / check-in workflow with a 14-day loan period
- Rules: no checkout when no copies are left, no duplicate loans of the same book, max 3 active loans per member
- Overdue tracking and a Rs 2/day fine, computed when the book comes back

## Design
```
gui.py          Tkinter view, thin, no rules
service.py      Business rules (limits, due dates, fines). Clock is injected, so tests can time-travel
repository.py   All SQL (SQLite). No rules
models.py       Dataclasses + LibraryError
```
Splitting the layers means the rules are unit-tested without a display or a real database
(`:memory:` SQLite), and the GUI could be swapped for a web UI without touching them.

## Run
```bash
uv venv && uv pip install pytest
.venv/bin/python -m pytest -q        # 11 tests
python3 -m library                   # launches the GUI, data stored in library.db
```
The GUI needs a Python build with working Tcl/Tk (the macOS system Python or python.org builds work;
some standalone Python builds ship without Tcl).

## Limitations / future work
- No authentication or librarian roles
- Fine is computed at return time and not tracked as paid/unpaid
- Single-user SQLite; no concurrent-access handling
