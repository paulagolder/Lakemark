"""start.py - starting the program: which club to open, then its window.

    run(data_dir, club="CwMBC")         # club: from --club; None: the default club

The club opened is the one asked for with --club, otherwise the settings' default club,
otherwise the first one. When --club names a club that is not there yet, the program offers to
make it, so a new club's launcher sets the club up the first time it is used. With no clubs at
all (a new data folder), it asks for the first one.

A data folder from before version 1.05 is first turned into an RMBC club folder (see
storage/club_store.py), which becomes the default club.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from ..model.club import Club
from ..storage.club_store import convert_old_folder, find_club, has_old_files, list_clubs
from ..storage.errors import StorageError
from ..storage.settings_store import (DEFAULT_TITLE, RMBC_LOGO_FILE, Settings, load_settings,
                                      old_title, save_settings)
from .app_icon import APP_CLASS, set_app_icon
from .club_dialog import NewClubDialog
from .front_window import FrontWindow


def run(data_dir, club: str | None = None) -> None:
    data_dir = Path(data_dir)
    root = tk.Tk(className=APP_CLASS)    # for the questions asked before a club's window opens
    root.withdraw()
    set_app_icon(root)
    root.title(DEFAULT_TITLE)
    try:
        settings = load_settings(data_dir)
        convert(root, settings)
        chosen = choose_club(root, settings, club)
    finally:
        root.destroy()
    while chosen is not None:
        window = FrontWindow(settings, chosen)
        window.mainloop()
        chosen = window.next_club


def convert(root: tk.Misc, settings: Settings) -> None:
    """Move a data folder from before 1.05 into an RMBC club folder, and make RMBC the
    default club."""
    if not has_old_files(settings.data_dir):
        return
    title = old_title(settings.data_dir)
    try:
        club = convert_old_folder(settings.data_dir, title, RMBC_LOGO_FILE)
    except StorageError as exc:
        messagebox.showerror(DEFAULT_TITLE, f"Could not move the club's files into its own "
                             f"folder:\n\n{exc}", parent=root)
        return
    if club is not None and not settings.default_club:
        settings.default_club = club.abbreviation
        save_settings(settings)


def choose_club(root: tk.Misc, settings: Settings, wanted: str | None) -> Club | None:
    """The club to open, or None to stop (no club, and none was made)."""
    data_dir = settings.data_dir
    if wanted:
        club = find_club(data_dir, wanted)
        if club is not None:
            return _remember_first(settings, club)
        names = ", ".join(c.abbreviation for c in list_clubs(data_dir)) or "none yet"
        if not messagebox.askyesno(
                DEFAULT_TITLE, f"There is no club {wanted} in {data_dir} (clubs: {names}).\n\n"
                f"Set up {wanted} now?", parent=root):
            return None
        return _remember_first(settings, NewClubDialog(root, data_dir, wanted.strip()).show())
    clubs = list_clubs(data_dir)
    club = find_club(data_dir, settings.default_club) if settings.default_club else None
    if club is None and clubs:
        club = clubs[0]
    if club is None:
        club = NewClubDialog(root, data_dir, message=(
            f"{DEFAULT_TITLE} keeps race results for a club. To start, give the club's "
            "abbreviation and title.")).show()
    return _remember_first(settings, club)


def _remember_first(settings: Settings, club: Club | None) -> Club | None:
    """With no default club yet, the first club opened becomes it."""
    if club is not None and not settings.default_club:
        settings.default_club = club.abbreviation
        save_settings(settings)
    return club
