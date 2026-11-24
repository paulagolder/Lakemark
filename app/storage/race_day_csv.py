"""race_day_csv.py - a race day as a CSV file, written by the race day window's Export CSV and
read back by Import CSV in the competition window.

    write_race_day_csv(path, RaceDayFile(race_day, club=..., ...))
    file = read_race_day_csv(path)               # a RaceDayFile

The file starts with a heading saying where the race day comes from and which version it is,
ending with when it was exported; then, after a blank line, the table: a heading row, then one
row for each place, numbered from 1:

    LakeMark race day
    Club,RMBC,Rugeley Model Boat Club
    Competition,DF95 2026
    Classes,DF95,Victoria
    Race day,Race Day 16-11-2026
    Date,16/11/2026
    Version,4,20/11/2026 18:02
    Exported,23/11/2026 14:05,LakeMark 1.12

    Row,Race A,Race B,Race C
    1,12,7,12
    2,7,62*,29/PAG
    ...

Version is the race day's version and when it was saved (see model/race_day.py). A file saved
again from a spreadsheet may use semicolons or tabs, have no Row column, or have empty cells at
the ends of rows; all are read. A file with no heading (from version 1.11) is refused: there is
no telling where it comes from.
"""

from __future__ import annotations

import csv
import datetime
from dataclasses import dataclass, field
from pathlib import Path

from .. import __version__
from ..model.race_day import RaceDay, format_date, parse_date
from .errors import StorageError

TITLE = "LakeMark race day"              # the file's first line
ROW_HEADING = "Row"
MAX_FILE_SIZE = 64 * 1024                # a full race day is well under 2 KB
_TIME_FORMAT = "%d/%m/%Y %H:%M"
_HEADINGS = ("Club", "Competition", "Classes", "Race day", "Date", "Version", "Exported")


@dataclass
class RaceDayFile:
    race_day: RaceDay                    # with its version and when it was saved
    club: str                            # the club's abbreviation
    club_title: str = ""
    competition: str = ""
    classes: list[str] = field(default_factory=list)
    exported: str = ""                   # when, as written: "23/11/2026 14:05"
    program: str = ""                    # what wrote it: "LakeMark 1.12"


def write_race_day_csv(path, file: RaceDayFile, exported: datetime.datetime | None = None) -> None:
    """Write the heading and the table, with its places numbered. exported: when (default now).
    Raises StorageError."""
    day = file.race_day
    exported = exported or datetime.datetime.now()
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows([
                [TITLE],
                ["Club", file.club, file.club_title],
                ["Competition", file.competition],
                ["Classes", *file.classes],
                ["Race day", day.name],
                ["Date", format_date(day.date)],
                ["Version", day.version, day.saved.strftime(_TIME_FORMAT) if day.saved else ""],
                ["Exported", exported.strftime(_TIME_FORMAT), f"LakeMark {__version__}"],
                [],
                [ROW_HEADING, *day.columns],
            ])
            writer.writerows([number, *row] for number, row in enumerate(day.rows, start=1))
    except OSError as exc:
        raise StorageError(f"Could not write {path}: {exc.strerror or exc}") from exc


def read_race_day_csv(path) -> RaceDayFile:
    """The race day in a file written by write_race_day_csv. Raises StorageError with a message
    for the user if the file cannot be read or is not a race day exported by LakeMark."""
    path = Path(path)
    table = _read_table(path)
    if not table or table[0][0] != TITLE:
        raise StorageError(f"{path.name} is not a race day exported by LakeMark 1.12 or later: it "
                           f"should start with the line \"{TITLE}\". Export it again with Export CSV "
                           f"in the race day's window.")
    heading: dict[str, list[str]] = {}
    table.pop(0)
    while table and table[0][0] in _HEADINGS:
        key, *values = table.pop(0)
        heading[key] = _trim(values)
    club = heading.get("Club", [])
    if not club or not club[0]:
        raise StorageError(f"{path.name} does not say which club it comes from.")
    if not table:
        raise StorageError(f"{path.name} has no table of sail numbers.")

    columns, rows = table[0], table[1:]
    if columns[0].lower() == ROW_HEADING.lower():            # the place numbers: not needed
        columns, rows = columns[1:], [row[1:] for row in rows]
    columns = _trim(columns)
    if not columns or not all(columns):
        raise StorageError(f"{path.name} has no race names above its sail numbers "
                           f"(they should start {ROW_HEADING},Race A,Race B ...).")
    try:
        day = RaceDay.from_table(_first(heading, "Race day"), columns, rows,
                                 parse_date(_first(heading, "Date")))
    except ValueError as exc:
        raise StorageError(f"{path.name}: {exc}") from exc
    version = heading.get("Version", [])
    day.version = int(version[0]) if version and version[0].isdigit() else 0
    day.saved = _time(version[1]) if len(version) > 1 else None
    exported = heading.get("Exported", [])
    return RaceDayFile(day, club[0], club_title=club[1] if len(club) > 1 else "",
                       competition=_first(heading, "Competition"),
                       classes=heading.get("Classes", []),
                       exported=exported[0] if exported else "",
                       program=exported[1] if len(exported) > 1 else "")


def _read_table(path: Path) -> list[list[str]]:
    """The file's rows, cells trimmed, blank rows left out."""
    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            raise StorageError(f"{path.name} is too big to be a race day.")
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="cp1252")       # saved by a Windows spreadsheet
        except (OSError, UnicodeDecodeError) as exc:
            raise StorageError(f"Could not read {path.name}: {exc}") from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path.name}: {exc.strerror or exc}") from exc
    rows = csv.reader(text.splitlines(), delimiter=_delimiter(text))
    return [row for row in ([cell.strip() for cell in row] for row in rows) if any(row)]


def _delimiter(text: str) -> str:
    """The separator the file uses: a comma, or a semicolon or tab from a spreadsheet. Judged on
    the first lines; the table's heading row has the most separators."""
    lines = text.splitlines()[:14] or [""]
    return max((",", ";", "\t"), key=lambda d: max(line.count(d) for line in lines))


def _time(text: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(text, _TIME_FORMAT)
    except ValueError:
        return None


def _trim(cells: list[str]) -> list[str]:
    """Without the empty cells a spreadsheet adds at the end of a row."""
    cells = list(cells)
    while cells and not cells[-1]:
        cells.pop()
    return cells


def _first(heading: dict[str, list[str]], key: str) -> str:
    values = heading.get(key, [])
    return values[0] if values else ""
