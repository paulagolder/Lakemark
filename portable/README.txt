LakeMark - portable copy
========================

For whoever sets up or looks after the USB stick. The LakeMark folder holds everything
the program needs:

    lakemark             the program for Linux. Double-click it, or run it from a terminal.
    lakemark.exe         the program for Windows. Double-click it.
    install-windows.bat  installs LakeMark on a Windows computer: see below.
    output/              the web pages you export: results, race days, reports.
                         This is the only folder you need to open.
    system/              the program's own files: settings, and a folder for each club
                         with its sailors, classes and competitions. Leave this folder
                         alone; the program looks after it.

Both programs use the same system and output folders, so the results are the same whichever
computer you use. Keep them together: copy or back up the whole LakeMark folder.

The program opens with the club chosen last (File > Choose club changes club). To open a
particular club, start it with the club's abbreviation:

    lakemark --club CwMBC            (lakemark.exe --club CwMBC on Windows)

Close the program before you unplug the USB stick.

The first time on a Windows computer, Windows may say "Windows protected your PC", as the
program is not code-signed: click More info, then Run anyway.

Installing on a Windows computer
--------------------------------
Double-click install-windows.bat. It makes a LakeMark folder in Documents, laid out like this
one, copies the program into it and puts LakeMark on the desktop and in the Start menu.

The first time, it copies the clubs and settings from the stick. From then on the computer keeps
its own results: what you enter there stays on the computer and does not go onto the stick. To
move a club between the two, use Club > Export club and File > Import club.

To update the program, run install-windows.bat again from a stick with the newer version: it
replaces the program and leaves the computer's clubs and results alone.

If the program will not start on Linux
--------------------------------------
Some Linux systems do not let programs run straight from a USB stick. Open a terminal and run

    bash /path/to/LakeMark/system/start-linux.sh

(drag start-linux.sh into the terminal window to type its path). It copies the program to a
temporary folder, runs it from there with the data on the stick, and tidies up afterwards.

In the Files app, double-clicking may open the program as a document instead of running it:
right-click it and choose "Run as a Program".
