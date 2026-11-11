"""front_window.py - the first window: one club's competitions.

    window = FrontWindow(settings, club)
    window.mainloop()
    window.next_club            # the club to open next (Club menu), or None if it was closed

The club's competition files (*.cxml, in its folder in the data folder) are listed here.
Double-click one (or select it and click Open) to open it in its own window. Edit changes a
competition's name, classes and so on (and its file name to match the name); New creates a
file in the club's folder. Delete takes it off the list by renaming the file to .cxml.deleted,
so it can be brought back.

The Club menu switches to another club (closing this club's windows), makes a new club,
changes this club's title and logo, and sets which club the program opens with. Export club
saves the club as a zip file, to hand it over to another race manager; Import club adds a club
from such a file.

The Info menu shows the help (F1) and About: the version, and where this club's files are.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..model.club import Club
from ..services.session import CompetitionSession
from ..storage.competition_store import (
    delete_competition,
    list_competitions,
    load_competition,
    suggested_filename,
    update_competition_details,
)
from ..storage.boat_class_store import boat_classes_or_defaults
from ..storage.club_store import list_clubs
from ..storage.club_transfer import export_club, export_filename, import_club
from ..storage.errors import StorageError
from ..storage.settings_store import Settings, save_settings
from .app_icon import APP_CLASS, set_app_icon
from .boat_classes_window import BoatClassesWindow
from .club_dialog import ClubDetailsDialog, NewClubDialog, load_logo
from .competition_window import CompetitionWindow
from .competition_dialog import CompetitionDialog
from .info_windows import AboutWindow, HelpWindow
from .sailors_window import SailorsWindow

COLUMNS = [("competition", "Competition", 220), ("classes", "Boat classes", 130), ("year", "Year", 60),
           ("days", "Race days", 80), ("file", "File", 200)]


class FrontWindow(tk.Tk):
    def __init__(self, settings: Settings, club: Club):
        super().__init__(className=APP_CLASS)
        set_app_icon(self)
        self.settings = settings
        self.club = club
        self.next_club: Club | None = None                   # set when switching club
        self.geometry("760x480")
        self.minsize(600, 360)
        self._logo: tk.PhotoImage | None = None

        self._paths: list[Path] = []                         # one per row in the list
        self._open: dict[Path, CompetitionWindow] = {}       # so a file is only open once

        self._build_menu()
        self._build_widgets()
        self._show_club()
        self.refresh()

    # -- building the window ----------------------------------------------------------------

    def _build_menu(self) -> None:
        # a row of menu buttons rather than Tk's own menu bar, which cannot put Info at the right
        menubar = ttk.Frame(self, padding=(4, 2, 4, 0))
        menubar.pack(side="top", fill="x")
        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")
        file_menu = self._menu_button(menubar, "File", "left")
        file_menu.add_command(label="New competition...", accelerator="Ctrl+N",
                              command=self.new_competition)
        file_menu.add_command(label="Refresh list", accelerator="F5", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Club sailors...", command=self.edit_sailors)
        file_menu.add_command(label="Boat classes...", command=self.edit_boat_classes)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", accelerator="Ctrl+Q", command=self.destroy)
        self.club_menu = self._menu_button(menubar, "Club", "left")
        self.club_menu.configure(postcommand=self._fill_club_menu)
        info_menu = self._menu_button(menubar, "Info", "right")
        info_menu.add_command(label="Help", accelerator="F1", command=self.show_help)
        info_menu.add_command(label="About Lakemark", command=self.show_about)
        self.bind("<Control-n>", lambda e: self.new_competition())
        self.bind("<F5>", lambda e: self.refresh())
        self.bind("<F1>", lambda e: self.show_help())
        self.bind("<Control-q>", lambda e: self.destroy())

    @staticmethod
    def _menu_button(menubar: ttk.Frame, label: str, side: str) -> tk.Menu:
        """A button on the menu row that drops down a menu; returns the menu, to fill."""
        button = tk.Menubutton(menubar, text=label, relief="flat", padx=8, pady=2)
        button.pack(side=side)
        menu = tk.Menu(button, tearoff=False)
        button.configure(menu=menu)
        return menu

    def _build_widgets(self) -> None:
        header = ttk.Frame(self, padding=(12, 10, 12, 4))
        header.pack(fill="x")
        self.logo_label = ttk.Label(header)
        self.logo_label.pack(side="left", padx=(0, 12))
        titles = ttk.Frame(header)
        titles.pack(side="left", fill="x", anchor="w")
        self.title_label = ttk.Label(titles, font=("TkDefaultFont", 16, "bold"))
        self.title_label.pack(anchor="w")
        ttk.Label(titles, text=f"{self.club.abbreviation} competitions in {self.club.folder}",
                  foreground="gray40").pack(anchor="w")

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w",
                  padding=(8, 2)).pack(side="bottom", fill="x")

        buttons = ttk.Frame(self, padding=(12, 0, 12, 8))
        buttons.pack(side="bottom", fill="x")
        self.open_button = ttk.Button(buttons, text="Open", command=self.open_selected)
        self.open_button.pack(side="left", padx=2)
        self.edit_button = ttk.Button(buttons, text="Edit...", command=self.edit_details)
        self.edit_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="New...", command=self.new_competition).pack(side="left", padx=2)
        self.delete_button = ttk.Button(buttons, text="Delete", command=self.delete_selected)
        self.delete_button.pack(side="left", padx=2)
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="left", padx=2)
        ttk.Button(buttons, text="Quit", command=self.destroy).pack(side="right", padx=2)

        body = ttk.Frame(self, padding=(12, 4, 12, 8))
        body.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(body, columns=[c[0] for c in COLUMNS], show="headings",
                                 selectmode="browse")
        for column_id, heading, width in COLUMNS:
            self.tree.heading(column_id, text=heading)
            self.tree.column(column_id, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._selection_changed())
        self.tree.bind("<Double-Button-1>", lambda e: self.open_selected())
        self.tree.bind("<Return>", lambda e: self.open_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())
        self.tree.bind("<F2>", lambda e: self.edit_details())

    def _show_club(self) -> None:
        """Show the club's title and logo (again, after they are changed)."""
        self.title(self.club.title)
        self.title_label.configure(text=self.club.title)
        self._logo = load_logo(self, self.club.logo)        # missing or unreadable: go without
        self.logo_label.configure(image=self._logo or "")
        self.logo_label.pack_configure(padx=(0, 12) if self._logo is not None else 0)

    # -- the list ---------------------------------------------------------------------------

    def refresh(self, select: Path | None = None) -> None:
        """Read the folder again and redraw the list, keeping (or moving to) a selection."""
        if select is None:
            index = self._selected_index()
            select = self._paths[index] if index is not None else None
        self.tree.delete(*self.tree.get_children())
        self._paths = []
        boat_classes = self._boat_classes()
        for path, competition, error in list_competitions(self.club.folder):
            if competition is None:
                values = ("(cannot be read)", "", "", "", path.name)
            else:
                classes = boat_classes.display_names(competition.classes)
                values = (competition.title, ", ".join(classes), competition.year,
                          len(competition.race_days), path.name)
            item = self.tree.insert("", "end", values=values)
            self._paths.append(path)
            if select is not None and path.resolve() == select.resolve():
                self.tree.selection_set(item)
                self.tree.see(item)
        if not self._paths:
            self.status_var.set("No competitions yet. Click New to start one.")
        self._selection_changed()

    def _selected_index(self) -> int | None:
        selection = self.tree.selection()
        return self.tree.index(selection[0]) if selection else None

    def _selection_changed(self) -> None:
        index = self._selected_index()
        for button in (self.open_button, self.edit_button, self.delete_button):
            button.state(["!disabled" if index is not None else "disabled"])
        if index is not None:
            self.status_var.set("Click Open (or double-click) to see its race days.")
        elif self._paths:
            count = len(self._paths)
            self.status_var.set(f"{count} competition{'s' if count != 1 else ''}. Select one to open it.")

    # -- opening and creating ---------------------------------------------------------------

    def open_selected(self) -> None:
        index = self._selected_index()
        if index is not None:
            self.open_path(self._paths[index])

    def open_path(self, path: Path) -> None:
        key = path.resolve()
        window = self._open.get(key)
        if window is not None and window.winfo_exists():     # already open: bring it forward
            window.deiconify()
            window.lift()
            window.focus_set()
            return
        try:
            session = CompetitionSession.open(path, self._boat_classes())
        except StorageError as exc:
            messagebox.showerror("Cannot open file", str(exc), parent=self)
            return
        self._open[key] = CompetitionWindow(self, session, self.settings, self.club,
                                            on_close=lambda: self._closed(key))

    def _closed(self, key: Path) -> None:
        self._open.pop(key, None)
        if self.winfo_exists():
            self.refresh()                # race day counts may have changed

    def new_competition(self) -> None:
        boat_classes = self._boat_classes()
        competition = CompetitionDialog(self, boat_classes=boat_classes).show()
        if competition is None:
            return
        path = self.club.folder / suggested_filename(competition)
        if path.exists():
            messagebox.showwarning("New competition", f"There is already a {competition.title} "
                                   f"competition ({path.name}). Open it from the list instead.",
                                   parent=self)
            self.refresh(select=path)
            return
        try:
            CompetitionSession.create(competition, path, boat_classes)
        except StorageError as exc:
            messagebox.showerror("Cannot create file", str(exc), parent=self)
            return
        self.refresh(select=path)
        self.open_path(path)

    # -- changing details and deleting ------------------------------------------------------

    def _is_open(self, path: Path, action: str) -> bool:
        window = self._open.get(path.resolve())
        if window is not None and window.winfo_exists():
            messagebox.showinfo(action, f"{path.name} is open. Close its window first.", parent=self)
            window.lift()
            return True
        return False

    def edit_details(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        path = self._paths[index]
        title = "Competition details"
        if self._is_open(path, title):
            return
        try:
            competition = load_competition(path)
        except StorageError as exc:
            messagebox.showerror(title, str(exc), parent=self)
            return
        details = CompetitionDialog(self, title=title, competition=competition,
                                    boat_classes=self._boat_classes()).show()
        if details is None or details.same_details(competition):
            return
        try:
            new_path = update_competition_details(path, details)
        except StorageError as exc:
            messagebox.showerror(title, str(exc), parent=self)
            self.refresh()
            return
        self.refresh(select=new_path)
        self.status_var.set(f"Saved {details.title} ({new_path.name}).")

    def delete_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
        path = self._paths[index]
        if self._is_open(path, "Delete competition"):
            return
        values = self.tree.item(self.tree.get_children()[index])["values"]
        name = values[0] if values[1] else path.name         # an unreadable file has no title
        count = values[3]
        days = f" and its {count} race day{'s' if count != 1 else ''}" if count else ""
        if not messagebox.askyesno(
                "Delete competition", f"Delete {name}{days}?\n\nIt will be taken off the "
                f"list. The file is kept as {path.name}.deleted in case you need it back.",
                icon="warning", parent=self):
            return
        try:
            delete_competition(path)
        except StorageError as exc:
            messagebox.showerror("Delete competition", str(exc), parent=self)
            return
        self.refresh()
        self.status_var.set(f"Deleted {path.name} (kept as {path.name}.deleted).")

    def edit_sailors(self) -> None:
        SailorsWindow(self, self.club).show()

    def edit_boat_classes(self) -> None:
        BoatClassesWindow(self, self.club).show()

    def _boat_classes(self):
        return boat_classes_or_defaults(self.club.classes_file)

    # -- the Info menu ----------------------------------------------------------------------

    def show_help(self) -> None:
        window = getattr(self, "_help", None)
        if window is not None and window.winfo_exists():     # already open: bring it forward
            window.lift()
            return
        self._help = HelpWindow(self)

    def show_about(self) -> None:
        AboutWindow(self, self.settings, self.club)

    # -- clubs ------------------------------------------------------------------------------

    def _fill_club_menu(self) -> None:
        """The Club menu, made afresh each time it opens, so it lists every club."""
        menu = self.club_menu
        menu.delete(0, "end")
        current = tk.StringVar(master=menu, value=self.club.abbreviation)
        self._club_choice = current                          # kept, or the tick is forgotten
        for club in list_clubs(self.settings.data_dir):
            label = (club.abbreviation if club.title == club.abbreviation
                     else f"{club.abbreviation}: {club.title}")
            menu.add_radiobutton(label=label, variable=current, value=club.abbreviation,
                                 command=lambda c=club: self.switch_club(c))
        menu.add_separator()
        menu.add_command(label="New club...", command=self.new_club)
        menu.add_command(label=f"{self.club.abbreviation} club details (title, logo)...",
                         command=self.edit_club)
        is_default = self.club.is_called(self.settings.default_club)
        menu.add_command(label=f"Open with {self.club.abbreviation} when the program starts",
                         state="disabled" if is_default else "normal", command=self.make_default)
        menu.add_separator()
        menu.add_command(label=f"Export {self.club.abbreviation} club...", command=self.export_club)
        menu.add_command(label="Import club...", command=self.import_club)

    def switch_club(self, club: Club) -> None:
        """Close this club's windows and open the club's. Its competitions are already saved."""
        if club.folder.resolve() == self.club.folder.resolve():
            return
        self.next_club = club
        self.destroy()

    def new_club(self) -> None:
        club = NewClubDialog(self, self.settings.data_dir).show()
        if club is not None and messagebox.askyesno(
                "New club", f"Made {club.abbreviation}, in {club.folder}.\n\nSwitch to it now? "
                "(This club's windows will close.)", parent=self):
            self.switch_club(club)

    def edit_club(self) -> None:
        if ClubDetailsDialog(self, self.club).show():
            self._show_club()

    def export_club(self) -> None:
        """Save the club (its folder) as a zip file, to hand it over to someone else."""
        name = filedialog.asksaveasfilename(
            parent=self, title=f"Export {self.club.abbreviation} club",
            initialfile=export_filename(self.club), defaultextension=".zip",
            filetypes=[("Zip files", "*.zip")])
        if not name:
            return
        try:
            path = export_club(self.club, name)
        except StorageError as exc:
            messagebox.showerror("Export club", str(exc), parent=self)
            return
        messagebox.showinfo("Export club", f"Saved {self.club.abbreviation}'s sailors, classes, "
                            f"logo and competitions to\n{path}\n\nThe other race manager chooses "
                            "Club > Import club... and picks this file.", parent=self)

    def import_club(self) -> None:
        """Add a club from a zip file made by Export club."""
        name = filedialog.askopenfilename(parent=self, title="Import club",
                                          filetypes=[("Zip files", "*.zip"), ("All files", "*")])
        if not name:
            return
        try:
            club = import_club(self.settings.data_dir, name)
        except StorageError as exc:
            messagebox.showerror("Import club", str(exc), parent=self)
            return
        if messagebox.askyesno("Import club", f"Imported {club.title} ({club.abbreviation}), "
                               f"into {club.folder}.\n\nSwitch to it now? (This club's windows "
                               "will close.)", parent=self):
            self.switch_club(club)

    def make_default(self) -> None:
        self.settings.default_club = self.club.abbreviation
        if save_settings(self.settings):
            self.status_var.set(f"The program will open with {self.club.abbreviation} from now on "
                                "(unless started with --club).")
        else:
            messagebox.showerror("Club", "Could not save the settings.", parent=self)
