"""club.py - a club that the program keeps results for, and the names of its files.

Each club has its own folder in the data folder, named by its abbreviation, and its files are
named by the abbreviation too:

    RMBC/
        RMBCClub.xml        the club's title (shown at the top of windows and web pages)
        RMBCSail.xml        the club's sailors
        RMBCClasses.xml     the club's boat classes
        RMBCLogo.png        the club's logo (or .gif), if it has one
        DF95_2026.cxml      the club's competitions
        ...

An abbreviation is 1 to MAX_ABBREVIATION letters or digits, such as RMBC or CwMBC. Clubs are
told apart ignoring case, so a launcher started with --club cwmbc finds CwMBC.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MAX_ABBREVIATION = 10
LOGO_TYPES = (".png", ".gif")            # what Tk 8.6 can show

_ABBREVIATION = re.compile(rf"[A-Za-z0-9]{{1,{MAX_ABBREVIATION}}}")


def abbreviation_problem(abbreviation: str) -> str | None:
    """Why this cannot be a club's abbreviation, or None if it can."""
    if not _ABBREVIATION.fullmatch(abbreviation):
        return (f"A club's abbreviation must be 1 to {MAX_ABBREVIATION} letters or digits, "
                "such as RMBC or CwMBC.")
    return None


@dataclass
class Club:
    abbreviation: str
    folder: Path
    title: str = ""             # blank: the abbreviation

    def __post_init__(self):
        self.folder = Path(self.folder)
        self.title = (self.title or "").strip() or self.abbreviation

    @property
    def details_file(self) -> Path:
        return self.folder / f"{self.abbreviation}Club.xml"

    @property
    def sailors_file(self) -> Path:
        return self.folder / f"{self.abbreviation}Sail.xml"

    @property
    def classes_file(self) -> Path:
        return self.folder / f"{self.abbreviation}Classes.xml"

    def logo_file(self, suffix: str) -> Path:
        return self.folder / f"{self.abbreviation}Logo{suffix}"

    @property
    def logo(self) -> Path | None:
        """The club's logo file, or None if it has none."""
        return next((path for path in map(self.logo_file, LOGO_TYPES) if path.is_file()), None)

    def is_called(self, abbreviation: str) -> bool:
        return self.abbreviation.casefold() == abbreviation.strip().casefold()
