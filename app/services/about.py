"""about.py - what the Info menu shows: the version, the facts for About, and the help text.

    version_text()                          'Lakemark 1.06 (4 November 2026)'
    about_facts(settings, club)             [("Version", "1.06"), ("Released", ...), ...]
    help_text()                             the help, from resources/help.txt
"""

from __future__ import annotations

import datetime
import platform
import sys
from pathlib import Path

from .. import __version__, __version_date__
from ..model.club import Club
from ..storage.competition_store import list_competitions
from ..storage.settings_store import Settings

NAME = "Lakemark"
HELP_FILE = Path(__file__).parent.parent / "resources" / "help.txt"

ABOUT_TEXT = """\
Lakemark keeps race results for radio-controlled model yachts: competitions
made of race days, each a small table of sail numbers, with the results so far
and web pages to share them. Each club has a folder of its own, so one race
manager can look after several clubs, and hand a club over to another.
Developed by Paul Golder, with Claude (Anthropic) as AI pair programmer."""


def version_date() -> str:
    """'4 November 2026'."""
    date = datetime.date.fromisoformat(__version_date__)
    return f"{date.day} {date:%B %Y}"


def version_text() -> str:
    """'Lakemark 1.06 (4 November 2026)'."""
    return f"{NAME} {__version__} ({version_date()})"


def about_facts(settings: Settings, club: Club) -> list[tuple[str, str]]:
    """The name and value of each fact Info > About lists, about this copy and the open club."""
    count = sum(1 for _ in list_competitions(club.folder))
    return [
        ("Version", __version__),
        ("Released", version_date()),
        ("Python", f"{platform.python_version()}  ({_tk_version()})"),
        ("System", f"{platform.system()} {platform.release()} ({platform.machine()})"),
        ("Club", club.abbreviation if club.title == club.abbreviation
         else f"{club.abbreviation}: {club.title}"),
        ("Competitions", str(count)),
        ("Club folder", str(club.folder)),
        ("Data folder", str(settings.data_dir)),
        ("Output folder", str(settings.club_output_dir(club.abbreviation))),
        ("Program", str(Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
                        .resolve())),
    ]


def help_text() -> str:
    """The help, or a note that it is missing."""
    try:
        return HELP_FILE.read_text(encoding="utf-8")
    except OSError:
        return "# Lakemark help\n\nThe help file is missing from the program.\n"


def _tk_version() -> str:
    try:
        import tkinter
        return f"Tk {tkinter.TkVersion}"
    except ImportError:
        return "no Tk"
