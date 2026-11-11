#!/usr/bin/env bash
# Build a single Linux program file, dist/lakemark, and a portable copy for a USB stick,
# dist/Lakemark/ (see portable/README.txt).
#
#     ./build_linux.sh
#
# Needs PyInstaller (pipx install pyinstaller) and tkinter (sudo apt install python3-tk).
# The program runs on this Linux version and newer ones, so build on the oldest you need.
# Data is not part of the program: each user's competitions stay in ~/.lakemark, or in
# the portable copy's system folder.

set -euo pipefail
cd "$(dirname "$0")"

echo "Running the tests..."
python3 -m unittest discover -s tests -t . -q

# RMBC's logo: Tk 8.6 cannot show SVG, so the program uses a PNG made from it (given to the
# RMBC club folder made from a data folder from before 1.05).
# Remade here when ImageMagick is installed; otherwise the PNG already in the project is used.
logo=app/resources/club_logo
if command -v convert >/dev/null && [ "$logo.svg" -nt "$logo.png" ]; then
    echo "Making the logo PNG..."
    convert -background none -density 384 "$logo.svg" -trim +repage -resize x56 -depth 8 "$logo.png"
fi

# Lakemark's icon: the PNG (for the windows) and the .ico (the Windows program file's icon, used
# by build_windows.bat) are made from lakemark.svg when ImageMagick is installed; otherwise the
# ones already in the project are used.
icon=app/resources/lakemark
if command -v convert >/dev/null && [ "$icon.svg" -nt "$icon.png" ]; then
    echo "Making the icon..."
    convert -background none -density 384 "$icon.svg" -resize 256x256 -depth 8 "$icon.png"
    convert -background none -density 384 "$icon.svg" -define icon:auto-resize=256,48,32,16 "$icon.ico"
fi

echo "Building..."
pyinstaller --noconfirm --clean --onefile --windowed \
    --name lakemark \
    --add-data "$(pwd)/app/resources:app/resources" \
    --distpath dist --workpath build --specpath build \
    main.py

# The portable copy, for a USB stick: the program and output/ on top, the rest in system/.
# system/ starts with no data; the program makes its settings there the first time it runs.
echo "Making the portable copy..."
portable=dist/Lakemark
rm -rf "$portable"
mkdir -p "$portable/output" "$portable/system"
cp dist/lakemark "$portable/"
cp portable/README.txt portable/start-linux.sh "$portable/system/"

echo
echo "Done: $(pwd)/dist/lakemark"
echo "Copy it anywhere (for example ~/.local/bin) and run it."
echo
echo "Portable copy: $(pwd)/$portable"
echo "Copy the whole folder to a USB stick, and add properties.xml and the club folders"
echo "(RMBC/, CwMBC/ ...) to its system folder: ./make_stick.sh does both."
