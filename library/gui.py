"""Tkinter front-end. Deliberately thin: every rule lives in LibraryService."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .models import LibraryError
from .repository import SqliteRepository
from .service import LibraryService


class LibraryApp(ttk.Frame):
    def __init__(self, master: tk.Tk, repo: SqliteRepository, service: LibraryService) -> None:
        super().__init__(master, padding=10)
        self.repo, self.service = repo, service
        self.pack(fill="both", expand=True)
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True)
        tabs.add(self._books_tab(tabs), text="Books")
        tabs.add(self._members_tab(tabs), text="Members")
        tabs.add(self._circulation_tab(tabs), text="Check out / in")
        tabs.add(self._overdue_tab(tabs), text="Overdue")

    # --- helpers -----------------------------------------------------------
    def _entry(self, parent: tk.Widget, label: str, row: int) -> tk.StringVar:
        var = tk.StringVar()
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=4, pady=2)
        ttk.Entry(parent, textvariable=var, width=30).grid(row=row, column=1, pady=2)
        return var

    def _guard(self, action: Callable[[], str]) -> None:
        """Run an action; show business-rule errors as dialogs instead of crashing."""
        try:
            messagebox.showinfo("Done", action())
        except (LibraryError, ValueError) as err:
            messagebox.showwarning("Cannot do that", str(err))
        except Exception as err:  # e.g. duplicate ISBN from SQLite
            messagebox.showerror("Error", str(err))

    # --- tabs --------------------------------------------------------------
    def _books_tab(self, parent: tk.Widget) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=8)
        title, author, isbn = (self._entry(tab, "Title", 0), self._entry(tab, "Author", 1),
                               self._entry(tab, "ISBN", 2))
        copies = self._entry(tab, "Copies", 3)
        copies.set("1")
        ttk.Button(tab, text="Add book", command=lambda: self._guard(
            lambda: f"Added book #{self.repo.add_book(title.get(), author.get(), isbn.get(), int(copies.get())).id}"
        )).grid(row=4, column=1, sticky="w", pady=4)

        query = self._entry(tab, "Search", 5)
        table = ttk.Treeview(tab, columns=("id", "title", "author", "avail"),
                             show="headings", height=8)
        for col, text in zip(table["columns"], ("ID", "Title", "Author", "Available")):
            table.heading(col, text=text)
        table.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=4)

        def search() -> None:
            table.delete(*table.get_children())
            for b in self.service.search(query.get()):
                table.insert("", "end", values=(b.id, b.title, b.author, f"{b.available}/{b.copies}"))
        ttk.Button(tab, text="Search", command=search).grid(row=6, column=1, sticky="w")
        return tab

    def _members_tab(self, parent: tk.Widget) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=8)
        name, email = self._entry(tab, "Name", 0), self._entry(tab, "Email", 1)
        ttk.Button(tab, text="Add member", command=lambda: self._guard(
            lambda: f"Added member #{self.repo.add_member(name.get(), email.get()).id}"
        )).grid(row=2, column=1, sticky="w", pady=4)
        return tab

    def _circulation_tab(self, parent: tk.Widget) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=8)
        book_id, member_id = self._entry(tab, "Book ID", 0), self._entry(tab, "Member ID", 1)

        def out() -> str:
            loan = self.service.check_out(int(book_id.get()), int(member_id.get()))
            return f"Checked out. Due {loan.due}"

        def back() -> str:
            loan = self.service.check_in(int(book_id.get()), int(member_id.get()))
            return f"Returned. Fine: Rs {loan.fine}"
        ttk.Button(tab, text="Check out", command=lambda: self._guard(out)).grid(row=2, column=0)
        ttk.Button(tab, text="Check in", command=lambda: self._guard(back)).grid(row=2, column=1)
        return tab

    def _overdue_tab(self, parent: tk.Widget) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=8)
        box = tk.Listbox(tab, width=70, height=10)
        box.pack(fill="both", expand=True)

        def refresh() -> None:
            box.delete(0, "end")
            for loan in self.service.overdue():
                box.insert("end", f"Book #{loan.book_id}  Member #{loan.member_id}  due {loan.due}")
        ttk.Button(tab, text="Refresh", command=refresh).pack(pady=4)
        return tab


def main(db_path: str = "library.db") -> None:
    repo = SqliteRepository(db_path)
    root = tk.Tk()
    root.title("Library Management System")
    LibraryApp(root, repo, LibraryService(repo))
    root.mainloop()
