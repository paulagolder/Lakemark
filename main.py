#!/usr/bin/env python3
"""Start the program:

    python main.py                   (opens the default club, in ~/.lakemark)
    python main.py --club CwMBC      (opens that club instead: one launcher for each club)
    python main.py --version         (prints the version and its date)
    python main.py --data FOLDER     (uses FOLDER as the data folder instead)

A portable copy has a system folder beside the program file, and uses that as its data folder
(see storage/settings_store.py).

The Windows program file has no console (it is built --windowed), so there --version and --help
show their text in a message box instead of printing it.
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from app import __version__, __version_date__

PROGRAM = "lakemark"                     # the program file's name
NAME = "Lakemark"


def version_text() -> str:
    """'Lakemark 1.04 (4 November 2026)'."""
    date = datetime.date.fromisoformat(__version_date__)
    return f"{NAME} {__version__} ({date.day} {date:%B %Y})"


def _show(text: str) -> None:
    """Print text, or show it in a message box when there is no console to print to."""
    if sys.stdout is not None:
        print(text)
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(NAME, text, parent=root)
    root.destroy()


class _Parser(argparse.ArgumentParser):
    def _print_message(self, message: str, file=None) -> None:
        if message:
            _show(message.rstrip("\n"))


class _VersionAction(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, help="show the version and its date, and exit")

    def __call__(self, parser, namespace, values, option_string=None):
        _show(version_text())
        parser.exit()


def main(argv: list[str] | None = None) -> None:
    parser = _Parser(prog=PROGRAM, description="Lakemark: race results for RC yachts.")
    parser.add_argument("-V", "--version", action=_VersionAction)
    parser.add_argument("--data", metavar="FOLDER", type=Path,
                        help="the data folder (default: a system folder beside the program, "
                             "otherwise ~/.lakemark)")
    parser.add_argument("--club", metavar="ABBREVIATION",
                        help="the club to open, such as RMBC or CwMBC (default: the club "
                             "chosen with Club > Open with ... when the program starts)")
    args = parser.parse_args(argv)

    from app.storage.settings_store import DATA_DIR, find_data_dir, move_old_data_dir
    from app.ui.start import run                    # only once a window is wanted
    data_dir = args.data or find_data_dir(program_dir())
    if data_dir == DATA_DIR:
        data_dir = move_old_data_dir()
    run(data_dir, args.club)


def program_dir() -> Path:
    """The folder the program file is in (the built file's, or this script's)."""
    return Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent


if __name__ == "__main__":
    main()
