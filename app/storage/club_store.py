"""club_store.py - the clubs in the data folder: finding, creating and changing them.

Each club is a folder in the data folder, holding <abbreviation>Club.xml (see model/club.py):

    <club>
      <title>Rugeley Model Boat Club</title>
    </club>

A sub folder without its Club.xml is not a club, and is left alone.

Before version 1.05 the data folder held one club's files (RMBC's) directly:
RMBCSail.xml, yachtclasses.xml and the competitions. convert_old_folder moves them into an
RMBC club folder the first time 1.05 runs.
"""

from __future__ import annotations

import os
import shutil
# Files are only read through xml_file.parse_xml, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from pathlib import Path

from ..model.boat_class import DEFAULT_BOAT_CLASSES, BoatClassList
from ..model.club import LOGO_TYPES, Club, abbreviation_problem
from ..model.member_list import MemberList
from .boat_class_store import save_boat_classes
from .errors import StorageError
from .member_store import save_members
from .xml_file import parse_xml, write_xml

OLD_CLUB = "RMBC"                        # whose files were in the data folder before 1.05
OLD_SAILORS_FILE = "RMBCSail.xml"
OLD_CLASSES_FILE = "yachtclasses.xml"
OLD_COMPETITIONS = "*.cxml*"             # competitions, with their .bak and .deleted copies


def load_club(folder) -> Club | None:
    """The club in this folder, or None if it is not a club's folder."""
    folder = Path(folder)
    club = Club(folder.name, folder)
    if abbreviation_problem(folder.name) or not club.details_file.is_file():
        return None
    try:
        club.title = (parse_xml(club.details_file).findtext("title") or "").strip() or club.abbreviation
    except (OSError, ET.ParseError):
        pass                             # an unreadable title: the abbreviation will do
    return club


def list_clubs(data_dir) -> list[Club]:
    """Every club in the data folder, in alphabetical order."""
    try:
        folders = [p for p in Path(data_dir).iterdir() if p.is_dir()]
    except OSError:
        return []
    clubs = [club for club in map(load_club, folders) if club is not None]
    return sorted(clubs, key=lambda c: c.abbreviation.casefold())


def find_club(data_dir, abbreviation: str) -> Club | None:
    """The club with this abbreviation (ignoring case), or None."""
    return next((c for c in list_clubs(data_dir) if c.is_called(abbreviation)), None)


def save_club(club: Club) -> None:
    """Write the club's details (its title). Raises StorageError."""
    root = ET.Element("club")
    ET.SubElement(root, "title").text = club.title
    write_xml(root, club.details_file, make_folder=True)


def create_club(data_dir, abbreviation: str, title: str = "") -> Club:
    """Make a new club's folder, with its details, no sailors yet and the default boat classes.

    Raises StorageError if the abbreviation is not allowed or the club is already there.
    """
    abbreviation = abbreviation.strip()
    problem = abbreviation_problem(abbreviation)
    if problem:
        raise StorageError(problem)
    existing = find_club(data_dir, abbreviation)
    if existing is not None:
        raise StorageError(f"There is already a club {existing.abbreviation}.")
    club = Club(abbreviation, Path(data_dir) / abbreviation, title)
    if club.folder.exists() and any(club.folder.iterdir()):
        raise StorageError(f"There is already a folder {club.folder} with other files in it.")
    save_club(club)
    save_members(MemberList(), club.sailors_file)
    save_boat_classes(BoatClassList(DEFAULT_BOAT_CLASSES), club.classes_file)
    return club


def set_logo(club: Club, image) -> Path:
    """Copy an image (PNG or GIF) into the club's folder as its logo, replacing any logo it
    had. Returns the logo's path. Raises StorageError."""
    image = Path(image)
    suffix = image.suffix.lower()
    if suffix not in LOGO_TYPES:
        raise StorageError("The logo must be a PNG or GIF picture. Save it as PNG first "
                           "(most picture programs can).")
    target = club.logo_file(suffix)
    try:
        shutil.copyfile(image, target)
    except shutil.SameFileError:
        pass
    except OSError as exc:
        raise StorageError(f"Could not copy {image.name}: {exc.strerror or exc}") from exc
    for other in LOGO_TYPES:
        if other != suffix:
            _remove(club.logo_file(other))
    return target


def remove_logo(club: Club) -> None:
    """Raises StorageError."""
    for suffix in LOGO_TYPES:
        _remove(club.logo_file(suffix))


def _remove(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise StorageError(f"Could not remove {path.name}: {exc.strerror or exc}") from exc


def has_old_files(data_dir) -> bool:
    """Whether the data folder still has a club's files directly in it (before 1.05)."""
    data_dir = Path(data_dir)
    return ((data_dir / OLD_SAILORS_FILE).exists() or (data_dir / OLD_CLASSES_FILE).exists()
            or any(data_dir.glob(OLD_COMPETITIONS)))


def convert_old_folder(data_dir, title: str = "", logo: Path | None = None) -> Club | None:
    """Move a data folder from before 1.05 into a club folder for RMBC: RMBCSail.xml,
    yachtclasses.xml (as RMBCClasses.xml) and the competitions, each with its backup. The
    club gets title, and a copy of logo.

    Returns the RMBC club, or None if there was nothing to move. Raises StorageError; whatever
    was moved before the error stays moved, and the rest is moved the next time.
    """
    data_dir = Path(data_dir)
    if not has_old_files(data_dir):
        return None
    club = find_club(data_dir, OLD_CLUB)
    if club is None:
        club = Club(OLD_CLUB, data_dir / OLD_CLUB, title)
        save_club(club)
    moves = [(data_dir / OLD_SAILORS_FILE, club.sailors_file),
             (data_dir / OLD_CLASSES_FILE, club.classes_file)]
    moves = [(old.with_name(old.name + end), new.with_name(new.name + end))
             for old, new in moves for end in ("", ".bak")]
    moves += [(path, club.folder / path.name) for path in sorted(data_dir.glob(OLD_COMPETITIONS))]
    for old, new in moves:
        if not old.is_file():
            continue
        if new.exists():
            raise StorageError(f"Cannot move {old.name} into {club.folder}: it already has one.")
        try:
            os.replace(old, new)
        except OSError as exc:
            raise StorageError(f"Could not move {old.name}: {exc.strerror or exc}") from exc
    if logo is not None and club.logo is None and Path(logo).is_file():
        set_logo(club, logo)
    return club
