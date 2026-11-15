"""club_dialog.py - chooses a club, asks for a new club's abbreviation and title, or changes a
club's title and logo.

    club = ChooseClubDialog(parent, data_dir, current).show()   # the Club chosen, or None
    club = NewClubDialog(parent, data_dir).show()           # the new Club (made on disk), or None
    changed = ClubDetailsDialog(parent, club).show()        # True if the title or logo changed

A club's abbreviation names its folder and files, so it cannot be changed once the club is
made. The logo is a PNG or GIF picture; it is copied into the club's folder, and shown at the
top of the windows and on exported web pages.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..model.club import MAX_ABBREVIATION, Club
from ..storage.club_store import create_club, list_clubs, remove_logo, save_club, set_logo
from ..storage.errors import StorageError

HINT = {"foreground": "gray40"}
LOGO_HEIGHT = 64                 # a bigger logo is shown smaller in the windows


def load_logo(master: tk.Misc, path: Path | None) -> tk.PhotoImage | None:
    """The logo as an image for the screen, made smaller if it is tall; None if there is no
    logo or it cannot be read."""
    if path is None:
        return None
    try:
        image = tk.PhotoImage(master=master, file=str(path))
    except tk.TclError:
        return None
    shrink = -(-image.height() // LOGO_HEIGHT)          # rounded up
    return image.subsample(shrink) if shrink > 1 else image


def club_label(club: Club) -> str:
    """'CwMBC: Chasewater Model Boat Club', or just the abbreviation when it has no title."""
    return club.abbreviation if club.title == club.abbreviation else f"{club.abbreviation}: {club.title}"


class ChooseClubDialog(tk.Toplevel):
    """Lists the clubs in the data folder (each folder holding its <club>Club.xml) to pick one."""

    def __init__(self, parent: tk.Misc, data_dir, current: Club | None = None):
        super().__init__(parent)
        self.title("Choose club")
        self.resizable(False, False)
        if parent.winfo_viewable():
            self.transient(parent)
        self.result: Club | None = None
        self.clubs = list_clubs(data_dir)

        frame = ttk.Frame(self, padding=16)
        frame.grid()
        ttk.Label(frame, text=f"Clubs in {data_dir}:", wraplength=380, justify="left").grid(
            row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(frame, width=48, height=min(max(len(self.clubs), 3), 12),
                                  activestyle="dotbox", exportselection=False)
        self.listbox.grid(row=1, column=0, sticky="we", pady=(4, 0))
        for club in self.clubs:
            self.listbox.insert("end", club_label(club))
        if self.clubs:
            index = next((i for i, c in enumerate(self.clubs)
                          if current is not None and c.is_called(current.abbreviation)), 0)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)
        else:
            ttk.Label(frame, text="There are no clubs yet: make one with File > New club,\n"
                                  "or add one from a zip file with File > Import club.",
                      **HINT).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.listbox.bind("<Double-Button-1>", lambda e: self._ok())

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, pady=(14, 0))
        self.ok_button = ttk.Button(buttons, text="OK", command=self._ok)
        self.ok_button.pack(side="left", padx=4)
        self.ok_button.state(["!disabled" if self.clubs else "disabled"])
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _ok(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        self.result = self.clubs[selection[0]]
        self.destroy()

    def show(self) -> Club | None:
        self.wait_visibility()
        self.grab_set()
        self.listbox.focus_set()
        self.wait_window(self)
        return self.result


class NewClubDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, data_dir, abbreviation: str = "", message: str = ""):
        super().__init__(parent)
        self.data_dir = Path(data_dir)
        self.title("New club")
        self.resizable(False, False)
        if parent.winfo_viewable():
            self.transient(parent)
        self.result: Club | None = None

        frame = ttk.Frame(self, padding=16)
        frame.grid()
        if message:
            ttk.Label(frame, text=message, wraplength=360, justify="left").grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.abbreviation_var = tk.StringVar(value=abbreviation)
        self.title_var = tk.StringVar()
        ttk.Label(frame, text="Abbreviation:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.abbreviation_entry = ttk.Entry(frame, textvariable=self.abbreviation_var, width=12)
        self.abbreviation_entry.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        ttk.Label(frame, text=f"such as RMBC or CwMBC: up to {MAX_ABBREVIATION} letters or digits.\n"
                              "It names the club's folder and files, and cannot be changed later.",
                  **HINT).grid(row=2, column=1, sticky="w", padx=(8, 0))
        ttk.Label(frame, text="Title:").grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(frame, textvariable=self.title_var, width=34).grid(row=3, column=1, sticky="w",
                                                                   padx=(8, 0), pady=(4, 0))
        ttk.Label(frame, text="shown on windows and web pages; blank: the abbreviation",
                  **HINT).grid(row=4, column=1, sticky="w", padx=(8, 0))
        ttk.Label(frame, text="The logo can be added afterwards, with Club > club details.",
                  **HINT).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(buttons, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

    def _ok(self) -> None:
        try:
            self.result = create_club(self.data_dir, self.abbreviation_var.get(), self.title_var.get())
        except StorageError as exc:
            messagebox.showwarning("New club", str(exc), parent=self)
            return
        self.destroy()

    def show(self) -> Club | None:
        self.wait_visibility()
        self.grab_set()
        self.abbreviation_entry.focus_set()
        self.wait_window(self)
        return self.result


class ClubDetailsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, club: Club):
        super().__init__(parent)
        self.club = club
        self.title(f"{club.abbreviation} club details")
        self.resizable(False, False)
        self.transient(parent)
        self.changed = False
        self._logo_image: tk.PhotoImage | None = None    # kept, or Tk forgets the picture

        frame = ttk.Frame(self, padding=16)
        frame.grid()
        ttk.Label(frame, text="Abbreviation:").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text=club.abbreviation, font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Label(frame, text=f"folder: {club.folder}", **HINT).grid(row=1, column=1, sticky="w",
                                                                    padx=(8, 0))
        ttk.Label(frame, text="Title:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.title_var = tk.StringVar(value=club.title)
        self.title_entry = ttk.Entry(frame, textvariable=self.title_var, width=34)
        self.title_entry.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        ttk.Label(frame, text="Logo:").grid(row=3, column=0, sticky="nw", pady=(8, 0))
        logo_frame = ttk.Frame(frame)
        logo_frame.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.logo_label = ttk.Label(logo_frame, **HINT)
        self.logo_label.pack(side="left", padx=(0, 12))
        ttk.Button(logo_frame, text="Choose picture...", command=self._choose_logo).pack(side="left")
        self.remove_button = ttk.Button(logo_frame, text="Remove", command=self._remove_logo)
        self.remove_button.pack(side="left", padx=4)
        ttk.Label(frame, text="a PNG or GIF picture; it is copied into the club's folder",
                  **HINT).grid(row=4, column=1, sticky="w", padx=(8, 0))

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, pady=(14, 0))
        ttk.Button(buttons, text="OK", command=self._ok).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self._show_logo()

    def _show_logo(self) -> None:
        self._logo_image = load_logo(self, self.club.logo)
        if self._logo_image is not None:
            self.logo_label.configure(image=self._logo_image, text="")
        else:
            self.logo_label.configure(image="", text="(none)" if self.club.logo is None
                                      else "(cannot be shown)")
        self.remove_button.state(["!disabled" if self.club.logo is not None else "disabled"])

    def _choose_logo(self) -> None:
        name = filedialog.askopenfilename(
            parent=self, title="Choose the club's logo",
            filetypes=[("PNG or GIF pictures", "*.png *.PNG *.gif *.GIF"), ("All files", "*")])
        if not name:
            return
        try:
            tk.PhotoImage(master=self, file=name)          # can it be shown at all?
        except tk.TclError:
            messagebox.showwarning("Logo", f"{Path(name).name} is not a PNG or GIF picture that "
                                   "can be shown. Save it as PNG first (most picture programs "
                                   "can), then choose that.", parent=self)
            return
        try:
            set_logo(self.club, name)
        except StorageError as exc:
            messagebox.showerror("Logo", str(exc), parent=self)
            return
        self.changed = True
        self._show_logo()

    def _remove_logo(self) -> None:
        try:
            remove_logo(self.club)
        except StorageError as exc:
            messagebox.showerror("Logo", str(exc), parent=self)
            return
        self.changed = True
        self._show_logo()

    def _ok(self) -> None:
        title = self.title_var.get().strip() or self.club.abbreviation
        if title != self.club.title:
            old, self.club.title = self.club.title, title
            try:
                save_club(self.club)
            except StorageError as exc:
                self.club.title = old
                messagebox.showerror("Club details", str(exc), parent=self)
                return
            self.changed = True
        self.destroy()

    def show(self) -> bool:
        self.wait_visibility()
        self.grab_set()
        self.title_entry.focus_set()
        self.wait_window(self)
        return self.changed
