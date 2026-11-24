"""settings_store.py - the settings: the data folder and its properties.xml.

The data folder is Documents/LakeMark/system by default (the same layout as a portable copy,
below). It holds a folder for each club (see model/club.py) and properties.xml, the settings for
every club:

    <properties>
      <default_club>RMBC</default_club>
      <default_rows>5</default_rows>
      <default_columns>4</default_columns>
      <output_folder>output</output_folder>
    </properties>

default_club is the club chosen last time, which the program opens with (unless it is started
with --club); blank, or a club no longer in the data folder: it opens with no club chosen.

output_folder is where Export HTML writes, in a sub folder for the club and one for the
competition (for example Documents/LakeMark/output/RMBC/DF95_2026/). ~ and $VARIABLES are
expanded. A relative folder ("output", the default) is in the folder that holds the data folder.

Before version 1.05 properties.xml also had the club's <title>; it is now in the club's own
folder, and old_title reads it from an old file so it can be moved there.

A portable copy (on a USB stick, say) keeps everything together:

    LakeMark/
        lakemark             the program
        output/              the exported web pages: the only folder a user needs
        system/              the data folder: properties.xml and a folder for each club

The program uses a system folder beside it as its data folder (find_data_dir), with the
default output_folder "output". A copy installed from a stick (install-windows.bat) is the same
folder in Documents, so it finds its data the same way; a program file anywhere else uses
Documents/LakeMark/system, the same data.

Before version 1.11 the data folder was ~/.lakemark, and before 1.04 ~/.pyraceresults:
move_old_data_dir moves the old one the first time.

The folder and file are created with these defaults the first time the program runs. A missing
or unreadable value falls back to its default, and numbers are kept within the limits in
model/limits.py.
"""

from __future__ import annotations

import os
import shutil
import sys
# Files are only read through xml_file.parse_xml, which refuses XML bombs.
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import dataclass
from pathlib import Path

from ..model.limits import DEFAULT_RACES, DEFAULT_ROWS, MAX_PLACES, MAX_RACES
from .xml_file import parse_xml



def documents_dir() -> Path:
    """The user's Documents folder (see _user_folder)."""
    return _user_folder("FDD39AD0-238F-46AF-ADB4-6C85480369C7", "DOCUMENTS", "Documents")


def downloads_dir() -> Path:
    """The user's Downloads folder (see _user_folder), or the home folder if there is none."""
    folder = _user_folder("374DE290-123F-4565-9164-39C4925E467B", "DOWNLOAD", "Downloads")
    return folder if folder.is_dir() else Path.home()


def _user_folder(windows_id: str, xdg_name: str, default: str) -> Path:
    """One of the user's own folders. Windows lets it be moved (to OneDrive, say), so ask Windows
    where it is (windows_id: its FOLDERID). A Linux desktop may give it a name in the user's
    language (~/Téléchargements), kept in ~/.config/user-dirs.dirs as XDG_<xdg_name>_DIR. Otherwise,
    and on macOS, it is ~/<default>."""
    if sys.platform == "win32":
        try:
            import ctypes
            import uuid
            folder_id = ctypes.create_string_buffer(uuid.UUID(windows_id).bytes_le, 16)
            path = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(folder_id, 0, None,
                                                         ctypes.byref(path)) == 0:
                try:
                    return Path(path.value)
                finally:
                    ctypes.windll.ole32.CoTaskMemFree(path)
        except (OSError, AttributeError, ValueError):
            pass
    elif sys.platform != "darwin":
        folder = _xdg_user_dir(xdg_name)
        if folder is not None:
            return folder
    return Path.home() / default


def _xdg_user_dir(name: str) -> Path | None:
    """XDG_<name>_DIR="$HOME/Downloads" from ~/.config/user-dirs.dirs, or None."""
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    try:
        lines = (config / "user-dirs.dirs").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    for line in lines:
        key, _, value = line.partition("=")
        if key.strip() == f"XDG_{name}_DIR":
            value = value.strip().strip('"').replace("$HOME", str(Path.home()))
            folder = Path(value)
            # "$HOME/" means the setting is off: the home folder itself is not the folder
            return folder if folder.is_absolute() and folder != Path.home() else None
    return None


LAKEMARK_DIR = documents_dir() / "LakeMark"     # laid out like a portable copy
DATA_DIR = LAKEMARK_DIR / "system"
OLD_DATA_DIRS = (Path.home() / ".lakemark",      # the data folder before version 1.11
                 Path.home() / ".pyraceresults")  # before version 1.04
PROPERTIES_FILE = "properties.xml"
DEFAULT_TITLE = "LakeMark"               # the program's windows, before a club is chosen
DEFAULT_OUTPUT_FOLDER = "~/Documents/LakeMark_output"   # for a data folder named with --data
# earlier defaults: nothing in the program sets the output folder, so a file holding one of these
# was never given another, and gets the default of this version
OLD_OUTPUT_FOLDERS = ("~/Documents/raceresult_output", "~/Documents/lakemark_output",
                      "~/Documents/Lakemark_output", "~/Documents/LakeMark_output")
SYSTEM_FOLDER = "system"                 # beside the program: a portable copy's data folder
PORTABLE_OUTPUT_FOLDER = "output"        # beside the program, in a portable copy
# RMBC's logo, made from club_logo.svg. Before 1.05 every copy showed it; now each club has
# its own, and this one is only given to the RMBC folder made from an old data folder.
RMBC_LOGO_FILE = Path(__file__).parent.parent / "resources" / "club_logo.png"


@dataclass
class Settings:
    data_dir: Path
    default_club: str = ""                           # the club chosen last; blank: none yet
    default_rows: int = DEFAULT_ROWS
    default_columns: int = DEFAULT_RACES             # races in a new race day
    output_folder: str = DEFAULT_OUTPUT_FOLDER       # as written in the file, perhaps with ~

    @property
    def output_dir(self) -> Path:
        """The output folder; a relative one is beside the data folder."""
        return self.data_dir.parent / os.path.expandvars(os.path.expanduser(self.output_folder))

    def club_output_dir(self, abbreviation: str) -> Path:
        """Where Export HTML writes for a club: a sub folder of the output folder."""
        return self.output_dir / abbreviation


def find_data_dir(program_dir) -> Path:
    """The system folder beside the program if there is one (a portable or installed copy),
    otherwise Documents/LakeMark/system."""
    system = Path(program_dir) / SYSTEM_FOLDER
    return system if system.is_dir() else DATA_DIR


def move_old_data_dir(new: Path = DATA_DIR, olds: tuple[Path, ...] = OLD_DATA_DIRS) -> Path:
    """Before version 1.11 the data folder was ~/.lakemark (and before 1.04, when the program
    was called pyraceresults, ~/.pyraceresults). Move the first one found to the new place the
    first time, so a user keeps their clubs and competitions. Returns the folder to use: the old
    one if it cannot be moved; the new one, and the old left alone, if both exist."""
    if new.exists():
        return new
    for old in olds:
        if old.is_dir():
            try:
                new.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old), str(new))
            except OSError:
                return old
            break
    return new


def _default_output(data_dir: Path) -> str:
    return PORTABLE_OUTPUT_FOLDER if data_dir.name == SYSTEM_FOLDER else DEFAULT_OUTPUT_FOLDER


def _output_folder(root: ET.Element, data_dir: Path) -> str:
    folder = (root.findtext("output_folder") or "").strip()
    return _default_output(data_dir) if not folder or folder in OLD_OUTPUT_FOLDERS else folder


def _number(root: ET.Element, tag: str, default: int, maximum: int) -> int:
    try:
        return min(max(int((root.findtext(tag) or "").strip()), 1), maximum)
    except ValueError:
        return default


def settings_from_xml(root: ET.Element, data_dir: Path) -> Settings:
    return Settings(
        data_dir=data_dir,
        default_club=(root.findtext("default_club") or "").strip(),
        default_rows=_number(root, "default_rows", DEFAULT_ROWS, MAX_PLACES),
        default_columns=_number(root, "default_columns", DEFAULT_RACES, MAX_RACES),
        output_folder=_output_folder(root, data_dir),
    )


def settings_to_xml(settings: Settings) -> ET.Element:
    root = ET.Element("properties")
    ET.SubElement(root, "default_club").text = settings.default_club
    ET.SubElement(root, "default_rows").text = str(settings.default_rows)
    ET.SubElement(root, "default_columns").text = str(settings.default_columns)
    ET.SubElement(root, "output_folder").text = settings.output_folder
    return root


def save_settings(settings: Settings) -> bool:
    """Write data_dir/properties.xml. False if it cannot be written (the settings still hold
    for this run)."""
    root = settings_to_xml(settings)
    ET.indent(root)
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(settings.data_dir / PROPERTIES_FILE, encoding="utf-8",
                                   xml_declaration=True)
    except OSError:
        return False
    return True


def old_title(data_dir) -> str:
    """The <title> in a properties.xml from before 1.05 (blank if none, or the default)."""
    try:
        title = (parse_xml(Path(data_dir) / PROPERTIES_FILE).findtext("title") or "").strip()
    except (OSError, ET.ParseError):
        return ""
    return "" if title in (DEFAULT_TITLE, "Lakemark", "RC Yacht Race Tables") else title


def load_settings(data_dir=DATA_DIR) -> Settings:
    """Read data_dir/properties.xml, creating the folder and a default file if they are missing.

    Never raises: if the file cannot be read or written, the defaults are used.
    """
    data_dir = Path(data_dir)
    path = data_dir / PROPERTIES_FILE
    defaults = Settings(data_dir, output_folder=_default_output(data_dir))
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        if not path.exists() and not save_settings(defaults):
            return defaults
        return settings_from_xml(parse_xml(path), data_dir)
    except (OSError, ET.ParseError):
        return defaults
