# LakeMark

Race results for RC yachts: enter and edit race results for radio-controlled model sailing yachts.

- The program keeps results for one or more **clubs**, such as RMBC and CwMBC (Chasewater), one
  at a time. Each club has its own folder of sailors, boat classes, competitions, title and logo,
  so one race manager can look after several clubs, and another club can start using it.
- A **competition** has a name, a year and one or more boat classes, and lives in one XML file in
  its club's folder. It holds up to **15 race days**.
- A **race day** has a date (typed as day/month/year, today's for a new one) and a name, which by
  default is made from the date ("Race Day 30-12-1978") and follows it until you change it. It is a
  small table: up to **6 races (columns, Race A, Race B ...) and 15 rows**.
- A competition's classes are typed as a list separated by commas ("DF65, Victoria"); each must be
  one of the club's classes (`RMBCClasses.xml`, say), typed by its key or full name in any case. They are
  stored as class ids without repeats (`classes="df65,victoria"`).
- Every race day is open to all the competition's classes, and shows them but cannot change them.
  Each cell is a **sail number**, which must belong to one of the club's sailors in one of those
  classes (see **Entering sail numbers** below).

## The data folder

Everything lives in `~/Documents/LakeMark` (created on first run), laid out like the LakeMark
folder on a USB stick: `output/` for exported web pages and `system/` as the data folder. On
Windows it is the Documents folder Windows reports, which may be in OneDrive. Before version 1.11
the data folder was `~/.lakemark`, and before 1.04 (when the program was called pyraceresults)
`~/.pyraceresults`; the first run of a newer version moves it to `~/Documents/LakeMark/system`.

    ~/Documents/LakeMark/
        output/                     exported web pages, a folder for each club
        system/                     the data folder
            properties.xml          settings for every club
            RMBC/                   one folder for each club, named by its abbreviation
                RMBCClub.xml        the club's title
                RMBCSail.xml        the club's sailors
                RMBCClasses.xml     the club's boat classes
                RMBCLogo.png        the club's logo (or .gif)
                DF95_2026.cxml      the club's competitions
                ...
            CwMBC/
                CwMBCClub.xml ...

- `properties.xml`: `default_club`, the club chosen last, which the program opens with; the default number of rows
  and columns for a new race day; and `output_folder`, where **Export HTML** writes (default
  `output`, beside the data folder; before version 1.11 it was `~/Documents/LakeMark_output`,
  and earlier `lakemark_output` or `raceresult_output`, and a properties.xml naming one of those
  now gets `output`), in a sub folder for each club.
- `<club>Club.xml`: the club's title, shown at the top of the windows and on web pages. Change it,
  and the logo, with **Club > club details**.
- `<club>Sail.xml`: the club sailors, one `<sail sailnumber="   01" boatclass="DF95" forename=".." surname=".." tag="PG" />` per boat (tag: see below). Edit it with the
  **Club > Club sailors...** menu in the competitions window, then click Save. "Show class" limits the list to one class.
- `<club>Classes.xml`: the boat classes, one `<boatclass key="df95" fullname="DF95" cypher="95" symbol="@" />`
  per class (a new club starts with DF65, RG65, DF95 and Victoria). Edit it with the
  **Club > Boat classes...** menu, then click Save.
- `<club>Logo.png` (or `.gif`): the club's logo. Choose it with **Club > club details >
  Choose picture...**, which copies it here. Tk can only show PNG and GIF pictures: save a JPG
  logo as PNG first.
- Competition files, named after the competition, like `Victoria_df65_competition_2026.cxml`.
  New competitions are saved here, and every `.cxml` file here is listed in the first window.

Before version 1.05 the data folder held RMBC's files directly (`RMBCSail.xml`,
`yachtclasses.xml`, the competitions, and the title in `properties.xml`). The first run of 1.05
moves them into an `RMBC` folder, with RMBC's logo, and makes RMBC the default club. A sailor's
`club="..."` and a competition's `clubs="..."` in those files are ignored: a club's sailors and
competitions are the ones in its folder.

## Clubs

The program opens with the club chosen last (`default_club` in `properties.xml`), or the one
given with `--club`:

    lakemark --club CwMBC

so a launcher (a desktop shortcut) for each club opens that club straight away. If the club named
is not there yet, the program offers to set it up. With no club chosen yet, or when the last one
is no longer in the data folder, the window is headed LakeMark, with LakeMark's icon, and the
Club menu is greyed out until a club is chosen.

The **File** menu in the competitions window chooses a club (**Choose club...** lists the clubs in
the data folder; changing club closes this club's competition windows, asking first if any are
open), makes a **New club**, and imports one (**Import club...**, below). The chosen club becomes
the heading, with its logo. The **Club** menu then starts a **New competition**, changes the
club's **details** (title and logo), edits its **Club sailors** and **Boat classes**, and exports
it (**Export club...**). A club's abbreviation names its folder and files, so it cannot be
changed; it is 1 to 10 letters or digits.

### Handing a club over

To pass a club on to another race manager, choose **Club > Export club...**. It saves the
club's folder as one zip file (`CwMBC_club_2026-11-04.zip`): its title, logo, sailors, classes
and competitions, with their backups. Your own settings (`properties.xml`), your other clubs
and the exported web pages stay behind.

The other race manager chooses **File > Import club...** (**Club > Import club...** before
version 1.10; it needs 1.05 or later) and picks the file, and the program changes to that club. Import only accepts a zip with one club folder in
it, and never overwrites a club they already have with the same abbreviation. Copying the
club's folder into their data folder by hand does the same.

Once the club is handed over, only one person should go on entering its results, or the two
copies will differ.

The first window lists every competition in the club's folder. Double-click one (or select it and click
**Open**) to open it in its own window. **Edit...** changes its name,
year, classes, races counted or HTML folder (the file is renamed to match the name); **New...**
starts a new competition;
**Delete** takes it off the list (the file is kept as `.cxml.deleted`, rename it back to restore it). In a competition's window, pick a
race day and click **Edit** (or double-click it). Saving the race day window writes the competition file
straight away.

## Help and About

The **Info** menu in the competitions window has **Help** (F1), a guide for race managers
(`app/resources/help.txt`), and **About LakeMark**: the version and its date, the Python and
system it runs on, the open club, and where its folder, the data folder and the output folder
are. **Copy** puts those facts on the clipboard, to send with a question.

## Running it

Needs Python 3.9 or newer with tkinter (included with the Windows and macOS installers from python.org;
on Debian/Ubuntu install `python3-tk`). Nothing else to install.

    python main.py                   # opens the default club, in ~/Documents/LakeMark/system
    python main.py --club CwMBC      # opens another club
    python main.py --version         # LakeMark 1.14 (24 November 2026)
    python main.py --data FOLDER     # uses another data folder

## Entering sail numbers

A race day is open to all the competition's classes, so a sail number may be more than one
eligible sailor's. As each number is typed the window says whose it is:

- **No match**: "Unrecognised sail", and the cell is marked.
- **One match**: that sailor.
- **More than one**: when the cursor leaves the cell (Enter, Tab ...), a list asks which, and the
  number is tagged with your choice: `62*` (a **class tag**, the class's symbol from
  the club's classes file) when the choices are one sailor in different classes, or `29/PAG` (a
  **sailor tag**) when they are different sailors. Save also asks for any still to choose.

Each sailor's tag is their initials unless changed in **Club sailors** (Tag). If two sailors with
the same sail number in different classes have the same initials, give one of them another tag,
such as PAG and PGU; the window will not accept a clashing one.

## Results so far

In a competition's window, the **Results** button offers two tables. Each has one row per
competitor: a club sailor, with every sail number they sailed in any of the classes ("440 / 23").
A sailor sails one boat at a time, so their boats are alternatives and all their races count together (the
race day window marks a sailor who appears twice in one race). A sail number that is no club
sailor's is a competitor of its own. Each row has the place, the points on each race day and how
many races were sailed. A finish earns its place in points (row 1 = 1st =
1 point, row 2 = 2 points ...), so fewer is better, and equal scores share a place.

- **Current results**: every sailor, ranked by their average points per race sailed, however many
  races they have sailed. Useful during the season, when not everyone can make every race day.
- **Final results**: only the sailors who have sailed the competition's **races counted**
  (`racecount`) or more, ranked by the points from their best that many races. It needs races
  counted to be set (Edit in the competitions list).

Click a column heading to sort by it; click it again to reverse.

**Report** gives a short text summary: the number of race days, races sailed and finishes, how many
different sailors have taken part (in each class), how many have qualified for the final results,
each race day's figures and the leading boats in the current results.
**Save...** writes it to a text file and **Copy** puts it on the clipboard.

## Web pages of the results

In the race day window, **Export HTML** writes the table as a web page, with each sailor's name under
their sail number. It goes in `output_folder` (see properties.xml), in the club's folder and the
competition's HTML folder (`directory`), for example
`~/Documents/LakeMark/output/RMBC/Victoria2026/Race_day_1.html`. Exporting
the same race day again replaces its page.

In a results window, **Export HTML** writes that table as `results_current.html` or
`results_final.html` in the same folder.

Each page is a single file (the club's title and logo included), ready to email, upload or print.

## Security check

`./security_check.sh` checks the code with Bandit (`pipx install bandit`) and writes the report
into the output folder, in `security/`. See [SECURITY.md](SECURITY.md) for what the program does
outside its own files and what the findings mean.

## Making the program files

Each is a single file with Python included, so it runs on computers without Python installed.
Data is not part of the program: replacing it with a new build never touches anyone's
data folder.

**Linux** (on Linux):

    pipx install pyinstaller         # once
    ./build_linux.sh                 # runs the tests, then builds dist/lakemark

It runs on the Linux version it was built on and newer ones, so build on the oldest one you need.

A Linux program file carries no icon of its own: a launcher (`.desktop` file) gives it one. Copy
`app/resources/lakemark.png` to `~/.local/share/icons/hicolor/256x256/apps/`, and put
`Icon=lakemark` and `StartupWMClass=LakeMark` in the launcher, so the menu, the desktop and the
taskbar all show it.

The build also makes a **portable copy** for a USB stick, `dist/LakeMark/`:

    LakeMark/
        lakemark             the program
        install-windows.bat  installs LakeMark on a Windows computer (below)
        output/              exported web pages: the only folder users need to open
        system/              the data folder (instead of ~/Documents/LakeMark/system),
                             README.txt and start-linux.sh

To make a stick, plug it in and run

    ./make_stick.sh /run/media/$USER/STICK     # data from ~/Documents/LakeMark/system (or name another)

It also puts the Windows program on the stick as `lakemark.exe`, so one stick works on Linux and
Windows with the same data. That cannot be built on Linux, so it is downloaded from this version's
GitHub release (and kept in `dist/`): release the version (tag and push it) before making sticks,
or the stick gets the Linux program only.

It builds the program if needed and copies the club folders and `properties.xml` into
`system/` (with `output_folder` set to `output`). On a stick that already has data it only updates the
program, leaving the data alone. It ends by saying whether the program runs straight from the
stick: Linux only runs `.exe`, `.bat` and `.com` files from FAT32 sticks, so on those use
`start-linux.sh` (below), or format the stick exFAT.

The program uses a `system` folder beside it as its data folder, and there the default
`output_folder` is `output` (a relative output folder is beside the data folder). Copy the whole
folder to the stick and put `properties.xml` and the club folders (`RMBC/`, `CwMBC/` ...) in
`system/`. `lakemark --club CwMBC` works from the stick too. If a stick will not let the program run,
`bash system/start-linux.sh` runs a temporary copy of it with the stick's data. `--data FOLDER`
picks any data folder by hand.

**Installing on Windows from a stick**: `install-windows.bat`, beside `lakemark.exe` on the stick,
makes `Documents\LakeMark` (the same layout: `lakemark.exe`, `output\`, `system\`) and puts
LakeMark on the desktop and in the Start menu. A new installation gets the stick's clubs and
settings; where the computer already has a `system\properties.xml`, only the program is replaced.
It saves downloading the program, which browsers and Windows often block, as it is not
code-signed (and a program copied from a stick carries no "downloaded from the internet" mark).

**Windows** (on Windows, with Python from python.org):

    py -m pip install pyinstaller    # once
    build_windows.bat                # runs the tests, then builds dist\lakemark.exe

The .exe is not code-signed, so Windows may warn "Windows protected your PC": click
**More info**, then **Run anyway**.

**Both at once, on GitHub**: push a version tag and GitHub builds both (on Ubuntu 22.04 and
Windows), runs the tests on each, and publishes them as a release to download:

    git tag -a v1.05 -m "LakeMark 1.05"
    git push origin v1.05

See `.github/workflows/release.yml`. It can also be run by hand from the Actions tab to check
the builds without publishing anything.

### Making a release from IntelliJ IDEA

First commit and push the changes, and run the program once from the Run button to check it.
Then:

1. **Make the tag.** Choose **Git > New Tag...**. Type the tag name, such as `v1.05` (`v` and
   the version in `app/__init__.py`), and the message `LakeMark 1.05`. Leave Commit blank, so
   the tag goes on the latest commit. Click **Create Tag**.
   (No New Tag in the Git menu? Open the Git tool window, bottom left, go to its **Log** tab,
   right-click the top commit and choose **New Tag...**.)
2. **Push the tag.** Choose **Git > Push...** (Ctrl+Shift+K), tick **Push tags** at the bottom
   (choose **All** if it offers a choice), and click **Push**.
3. **Wait for the build.** On GitHub, the repository's **Actions** tab shows it running. A few
   minutes later the **Releases** page has the Linux and Windows files to download.

Or paste the two lines above into IntelliJ's **Terminal** tab (bottom of the window).

For the next version, change `__version__` and `__version_date__` in `app/__init__.py` first,
and commit that.

In the race day window, **Enter**, **Tab** or **Down** moves down the column (adding a row at the bottom until
there are 15, then moving to the top of the next column); **Shift+Tab** or **Up** goes back.
**Add row / Add column** grow the table, up to the limits.

## Project layout

    main.py                     starts the program
    app/
        model/                  the data classes: no screen, no files
            limits.py           how many races, places and race days; the year range
            boat_class.py       boat classes, and matching them ("DF 95" = "DF95")
            sail_number.py      matching, sorting and writing sail numbers ("1" = "01")
            race.py             Race: its name and finishers in order (place = points)
            race_day.py         RaceDay: a name, a date and its races, also seen as a table
            club.py             Club: a club's abbreviation, title, folder and the names of its files
            competition.py      Competition: name, year, classes, races counted, race days
            sailor.py           Sailor: one club boat
            member_list.py      MemberList: the club sailors
            sail_entry.py       SailResolver: which sailor an entry ("12", "12@", "29/PAG") means; checks race days
            results.py          Results: each competitor's races and points; the current and final tables
            summary.py          CompetitionSummary: the figures for the report
        storage/                reading and writing files
            errors.py           StorageError, with a message that can be shown to the user
            xml_file.py         writes a file safely, keeping a .bak
            competition_store.py  competition (.cxml) files
            club_store.py       the club folders: finding, making, title and logo; moving pre-1.05 files
            club_transfer.py    a club as a zip file: Export club and Import club
            race_day_csv.py     a race day as a CSV file, with a heading: Export CSV and Import CSV
            member_store.py     a club's sailors, RMBCSail.xml
            boat_class_store.py a club's boat classes, RMBCClasses.xml
            settings_store.py   Settings: the data folder and properties.xml
        services/               working with the model (no screen)
            session.py          an open file: every change is saved at once, and undone if saving fails
            scoring.py          works out the results over all race days, and the current and final tables
            results_table.py    the columns and scoring note shared by the results window and page
            html_export.py      a race day, or the results, as a web page
            report.py           the text summary of a competition (Report)
            race_day_import.py  Import CSV: add a race day, replace it with a later version, or refuse it
            about.py            the version, the facts Info > About shows, and the help text
        ui/                     the windows
            start.py            which club to open (--club, the default, or a new one), then its window
            front_window.py     the first window: a club's competitions, and the File and Club menus
            club_dialog.py      Choose club, New club, and a club's details (title and logo)
            competition_dialog.py  asks for a competition's details (New and Edit)
            competition_window.py  one competition: its race days and a preview
            race_day_window.py  enter or edit one race day's table
            grid_navigation.py  where Enter/Tab moves to in that table
            results_window.py   the current or final results (Results in a competition's window)
            report_window.py    the text summary (Report in a competition's window)
            info_windows.py     the Info menu's Help and About windows
            browser.py          opens an exported page in the web browser
            sailors_window.py   the Club sailors window
            boat_classes_window.py  the Boat classes window
            sail_chooser.py     asks which sailor an ambiguous sail number means
            app_icon.py         the LakeMark icon on every window
        resources/
            help.txt            the text of Info > Help (keep it in step with this README)
            lakemark.svg        LakeMark's icon; lakemark.png (the windows' icon) and lakemark.ico
                                (the Windows program file's) are made from it by build_linux.sh
            club_logo.svg       RMBC's logo; club_logo.png is made from it by build_linux.sh, and
                                given to the RMBC folder made from a pre-1.05 data folder
    tests/                      the same layout as app/: python -m unittest discover -s tests -t .

The layers only call downwards: ui uses services, storage and model; services use storage and
model; storage uses model; model uses nothing else. Everything except ui/ is tested without
needing a screen. To change a limit (races, rows, race days), edit `app/model/limits.py`.

## The file

    <competition year="2026" name="Victoria_df65_competition_2026" racecount="24"
                 directory="Victoria2026" classes="df65,victoria" version="3">
      <raceday name="Race day 1" date="2026-10-10">
        <race name="Race A">
          <sail>12</sail>
          <sail>7</sail>
        </race>
        ...
      </raceday>
    </competition>

A competition holds race days, a race day holds races, and a race holds sail numbers in
finishing order (the first `<sail>` came 1st). An empty `<sail />` is a place left empty.
`classes` is a list separated by commas of the class ids from the club's classes file, and
every race day is open to all of them. `racecount` may be left out (every race counts). A race day's `date` is year-month-day and may be left out.

Older files still open and are saved in this layout the next time they change. Versions 1 and 2
have a single `class="DF95"` and no name (the name becomes "DF95 2026"); version 1 stores each race
day as a table of `<columns>` and `<row>`s.

Each save keeps the previous version beside it as `DF95_2026.cxml.bak`.
