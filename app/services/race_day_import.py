"""race_day_import.py - what Import CSV does with a race day read from a CSV file
(storage/race_day_csv.py): add it, replace a race day with it, or refuse it.

    plan = plan_import(file, club, class_names, competition)    # raises ImportRefused

Only consistent imports are accepted. The file's heading says which club and classes it comes
from: sail numbers belong to a club's sailors in the competition's classes, so a race day from
another club, or raced in classes this competition does not have, is refused.

A race day is the same one as a race day in the competition when it has the same name (with
dated names, "Race Day 16-11-2026", that means the same date). Then the versions decide
(model/race_day.py):

    no race day of that name                     add it
    the file's is a later version                replace the race day with it
    the same version, and the same race day      nothing to do: it is up to date
    an earlier version, or the same version      replace it only if the user is sure
      with different results (both edited)

Added or replacing, it opens in the race day window first, to check before it is saved.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..model.competition import Competition
from ..model.limits import MAX_RACE_DAYS
from ..model.race_day import RaceDay
from ..storage.race_day_csv import RaceDayFile


class ImportRefused(Exception):
    """The race day cannot be imported here. The message says why, for the user."""


@dataclass
class ImportPlan:
    race_day: RaceDay                    # the file's, to open in the race day window
    replace: int | None                  # the index of the race day it replaces; None: added
    question: str = ""                   # to ask before going on ("": nothing to ask)


def plan_import(file: RaceDayFile, club: str, class_names: list[str],
                competition: Competition) -> ImportPlan:
    """What importing file into this competition of the club (its abbreviation), with these
    classes (their names), does. Raises ImportRefused, saying why, when it is not allowed or
    there is nothing to do."""
    day = file.race_day
    if file.club.casefold() != club.casefold():
        source = f"{file.club} ({file.club_title})" if file.club_title else file.club
        raise ImportRefused(f"{day.name} comes from another club, {source}. Its sail numbers are "
                            f"that club's sailors, so it cannot be imported into a competition "
                            f"of {club}.")
    ours = {c.casefold() for c in class_names}
    others = [c for c in file.classes if c.casefold() not in ours]
    if others or not file.classes:
        raise ImportRefused(f"{day.name} was raced in {', '.join(file.classes) or 'no classes'}, "
                            f"and this competition is for {', '.join(class_names)}, so it cannot "
                            f"be imported here.")

    index = next((i for i, d in enumerate(competition.race_days) if _same_name(d, day)), None)
    if index is None:
        if competition.is_full:
            raise ImportRefused(f"This competition already has {MAX_RACE_DAYS} race days, the "
                                f"most it can have.")
        return ImportPlan(day, None)

    ours_day = competition.race_days[index]
    if day.version > ours_day.version:
        return ImportPlan(day, index)
    if day.version == ours_day.version and day == ours_day:
        raise ImportRefused(f"{day.name} is already up to date in this competition "
                            f"({ours_day.version_text}).")
    why = ("The file holds an earlier version than this competition's."
           if day.version < ours_day.version else
           "The file and this competition hold different results under the same version: "
           "the race day has been changed in both since it was last copied.")
    return ImportPlan(day, index, question=(
        f"This competition already has {day.name}.\n\n"
        f"This competition: {ours_day.version_text}\n"
        f"The file: {day.version_text}\n\n"
        f"{why} Replace this competition's race day with the file's?"))


def source_text(file: RaceDayFile) -> str:
    """Where the file comes from, for the window's title:
    'RMBC, DF95 2026, version 4, exported 23/11/2026 14:05'."""
    parts = [file.club, file.competition, f"version {file.race_day.version}",
             f"exported {file.exported}" if file.exported else ""]
    return ", ".join(p for p in parts if p)


def _same_name(a: RaceDay, b: RaceDay) -> bool:
    return " ".join(a.name.split()).casefold() == " ".join(b.name.split()).casefold()
