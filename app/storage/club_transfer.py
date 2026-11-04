"""club_transfer.py - a club as a single zip file, to hand it over to another race manager.

    path = export_club(club, "CwMBC_club_2026-11-04.zip")
    club = import_club(data_dir, path)

The zip holds the club's folder and every file in it: its details, sailors, classes, logo and
competitions, with their backups (.bak) and deleted competitions (.cxml.deleted):

    CwMBC/
        CwMBCClub.xml
        CwMBCSail.xml
        ...

Importing puts the folder into the data folder, where the program finds it like any other club.
A zip is only imported if it is one club's folder (with its Club.xml) and nothing else: no
other folders, no names that lead outside it, and not too big. A club that is already there
(the same abbreviation, ignoring case) is never overwritten.
"""

from __future__ import annotations

import datetime
import os
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from ..model.club import Club, abbreviation_problem
from .club_store import find_club, load_club
from .errors import StorageError

MAX_FILES = 2_000                   # a club has a few dozen files
MAX_BYTES = 200_000_000             # in all, unpacked; a club is well under 1 MB plus its logo
_SKIPPED = (".tmp",)                # half-written files, never part of a club


def export_filename(club: Club, today: datetime.date | None = None) -> str:
    """'CwMBC_club_2026-11-04.zip'."""
    return f"{club.abbreviation}_club_{(today or datetime.date.today()).isoformat()}.zip"


def export_club(club: Club, path) -> Path:
    """Write the club's folder to a zip file at path. Raises StorageError."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    try:
        files = sorted(p for p in club.folder.iterdir()
                       if p.is_file() and not p.name.endswith(_SKIPPED))
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
            for file in files:
                archive.write(file, f"{club.abbreviation}/{file.name}")
        os.replace(tmp, path)
    except OSError as exc:
        raise StorageError(f"Could not write {path.name}: {exc.strerror or exc}") from exc
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
    return path


def _club_files(archive: zipfile.ZipFile) -> tuple[str, list[zipfile.ZipInfo]]:
    """The club's abbreviation and the files to unpack. Raises StorageError if the zip is not
    one club's folder."""
    members = [m for m in archive.infolist() if not m.is_dir()]
    if not members:
        raise StorageError("The zip file is empty.")
    if len(members) > MAX_FILES or sum(m.file_size for m in members) > MAX_BYTES:
        raise StorageError("The zip file is too big to be a club.")
    folders = set()
    for member in members:
        parts = PurePosixPath(member.filename).parts
        if (len(parts) != 2 or "\\" in member.filename or ":" in member.filename
                or parts[1] in (".", "..")):
            raise StorageError("The zip file should hold one club folder with its files "
                               f"directly in it; it has {member.filename}.")
        folders.add(parts[0])
    if len(folders) != 1:
        raise StorageError(f"The zip file holds more than one folder: {', '.join(sorted(folders))}.")
    abbreviation = folders.pop()
    if abbreviation_problem(abbreviation) or f"{abbreviation}/{abbreviation}Club.xml" not in {
            m.filename for m in members}:
        raise StorageError(f"The zip file is not a club exported from Lakemark (no "
                           f"{abbreviation}/{abbreviation}Club.xml in it).")
    return abbreviation, members


def import_club(data_dir, path) -> Club:
    """Unpack a club's zip file into the data folder and return the club.

    Raises StorageError if it is not a club's zip file, or the club is already there.
    """
    data_dir, path = Path(data_dir), Path(path)
    try:
        with zipfile.ZipFile(path) as archive:
            abbreviation, members = _club_files(archive)
            existing = find_club(data_dir, abbreviation)
            if existing is not None:
                raise StorageError(f"There is already a club {existing.abbreviation} in "
                                   f"{data_dir}. Its folder is never overwritten: move or rename "
                                   f"{existing.folder} first if this one should replace it.")
            target = data_dir / abbreviation
            if target.exists():
                raise StorageError(f"There is already a folder {target}.")
            data_dir.mkdir(parents=True, exist_ok=True)
            # Unpacked beside the data's clubs first, then moved into place, so a failure
            # part-way through never leaves half a club.
            with tempfile.TemporaryDirectory(dir=data_dir, prefix=".import-") as tmp:
                folder = Path(tmp) / abbreviation
                folder.mkdir()
                for member in members:
                    with archive.open(member) as source, \
                            open(folder / PurePosixPath(member.filename).name, "wb") as copy:
                        shutil.copyfileobj(source, copy)
                os.replace(folder, target)
    except zipfile.BadZipFile:
        raise StorageError(f"{path.name} is not a zip file.") from None
    except OSError as exc:
        raise StorageError(f"Could not import {path.name}: {exc.strerror or exc}") from exc
    club = load_club(target)
    if club is None:                     # cannot happen: its Club.xml was checked above
        raise StorageError(f"{target} is not a club folder.")
    return club
