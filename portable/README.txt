Lakemark - portable copy
========================

For whoever sets up or looks after the USB stick. The Lakemark folder holds everything
the program needs:

    lakemark             the program for Linux. Double-click it, or run it from a terminal.
    lakemark.exe         the program for Windows. Double-click it.
    output/              the web pages you export: results, race days, reports.
                         This is the only folder you need to open.
    system/              the program's own files: settings, and a folder for each club
                         with its sailors, classes and competitions. Leave this folder
                         alone; the program looks after it.

Both programs use the same system and output folders, so the results are the same whichever
computer you use. Keep them together: copy or back up the whole Lakemark folder.

The program opens with the default club (the Club menu switches club, and sets which one it
opens with). To open a particular club, start it with the club's abbreviation:

    lakemark --club CwMBC            (lakemark.exe --club CwMBC on Windows)

Close the program before you unplug the USB stick.

The first time on a Windows computer, Windows may say "Windows protected your PC", as the
program is not code-signed: click More info, then Run anyway.

If the program will not start on Linux
--------------------------------------
Some Linux systems do not let programs run straight from a USB stick. Open a terminal and run

    bash /path/to/Lakemark/system/start-linux.sh

(drag start-linux.sh into the terminal window to type its path). It copies the program to a
temporary folder, runs it from there with the data on the stick, and tidies up afterwards.

In the Files app, double-clicking may open the program as a document instead of running it:
right-click it and choose "Run as a Program".
