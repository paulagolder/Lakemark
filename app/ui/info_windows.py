"""info_windows.py - the Info menu's windows: Help and About.

    HelpWindow(parent)                      the help (resources/help.txt), to read beside the program
    AboutWindow(parent, settings, club)     the version, this copy's folders and the open club

In the help text a line starting "# " is a heading, and an indented line is shown as typed.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..model.club import Club
from ..services.about import ABOUT_TEXT, NAME, about_facts, help_text, version_text
from ..storage.settings_store import Settings
from .club_dialog import load_logo


class HelpWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title(f"{NAME} help")
        self.geometry("680x560")
        self.minsize(420, 300)

        bar = ttk.Frame(self, padding=(12, 0, 12, 12))
        bar.pack(side="bottom", fill="x")
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right", padx=2)

        body = ttk.Frame(self, padding=12)
        body.pack(fill="both", expand=True)
        view = tk.Text(body, wrap="word", padx=12, pady=8, spacing1=2, spacing3=4,
                       font=("TkDefaultFont", 10), relief="flat")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=view.yview)
        view.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        view.pack(side="left", fill="both", expand=True)
        view.tag_configure("heading", font=("TkDefaultFont", 13, "bold"), spacing1=10)
        view.tag_configure("code", font=("TkFixedFont", 10), lmargin1=24, lmargin2=24)
        view.tag_configure("item", lmargin1=8, lmargin2=20)
        for line in help_text().splitlines():
            if line.startswith("# "):
                view.insert("end", line[2:] + "\n", "heading")
            elif line.startswith("    "):
                view.insert("end", line.strip() + "\n", "code")
            elif line.startswith("- "):
                view.insert("end", "• " + line[2:] + "\n", "item")
            elif line:
                view.insert("end", line + "\n")
        view.configure(state="disabled")             # to read, not for editing

        self.bind("<Escape>", lambda e: self.destroy())
        view.focus_set()


class AboutWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, settings: Settings, club: Club):
        super().__init__(parent)
        self.title(f"About {NAME}")
        self.resizable(False, False)
        if parent.winfo_viewable():
            self.transient(parent)

        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)
        header = ttk.Frame(frame)
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._logo = load_logo(self, club.logo)      # kept, or Tk forgets the picture
        if self._logo is not None:
            ttk.Label(header, image=self._logo).pack(side="left", padx=(0, 12))
        ttk.Label(header, text=version_text(), font=("TkDefaultFont", 14, "bold")).pack(
            side="left")

        facts = about_facts(settings, club)
        bold = ("TkDefaultFont", 10, "bold")
        row = 1
        for name, value in facts:
            ttk.Label(frame, text=name, font=bold).grid(row=row, column=0, sticky="w",
                                                        padx=(0, 12), pady=1)
            ttk.Label(frame, text=value).grid(row=row, column=1, sticky="w", pady=1)
            row += 1
        ttk.Label(frame, text=ABOUT_TEXT, justify="left").grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(12, 0))

        bar = ttk.Frame(frame)
        bar.grid(row=row + 1, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(bar, text="Copy", command=self.copy).pack(side="left", padx=2)
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="left", padx=2)
        self._text = version_text() + "\n" + "\n".join(
            f"{name}: {value}" for name, value in facts)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self.destroy())
        self.focus_set()

    def copy(self) -> None:
        """The facts on the clipboard, to send with a question or a problem."""
        self.clipboard_clear()
        self.clipboard_append(self._text)
