"""app_icon.py - the program's own icon, for the title bar and taskbar of every window.

    root = tk.Tk(className=APP_CLASS)
    set_app_icon(root)

APP_CLASS is the window class a Linux desktop matches to a launcher (StartupWMClass=Lakemark),
so the taskbar shows the launcher's icon. The icon is resources/lakemark.png, made from
lakemark.svg by build_linux.sh (lakemark.ico, from the same drawing, is the Windows program
file's icon).
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

APP_CLASS = "Lakemark"
ICON_FILE = Path(__file__).parent.parent / "resources" / "lakemark.png"


def set_app_icon(root: tk.Tk) -> None:
    """Give root's windows, and every window opened from it, the Lakemark icon; without the
    file (or if Tk cannot read it) they keep the desktop's own."""
    try:
        image = tk.PhotoImage(master=root, file=str(ICON_FILE))
    except tk.TclError:
        return
    root._app_icon = image                     # kept, or Tk forgets the picture
    root.iconphoto(True, image)
