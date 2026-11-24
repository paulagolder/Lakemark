#!/usr/bin/env bash
# Make the stick zip for a GitHub release: everything a LakeMark stick needs, with no club data.
#
#     ./make_stick_zip.sh FOLDER VERSION      FOLDER holds lakemark-VERSION-linux and
#                                             lakemark-VERSION-windows.exe
#
# Writes FOLDER/lakemark-VERSION-stick.zip. Unzipped onto a USB stick (formatted exFAT), it is:
#
#     LakeMark quick-start.pdf
#     LakeMark/
#         lakemark             the program for Linux
#         lakemark.exe         the program for Windows
#         install-windows.bat  installs LakeMark on a Windows computer, in Documents\LakeMark
#         output/              exported web pages
#         system/              README.txt and start-linux.sh; no data
#
# With no data in system/, the first start makes the sample club, LMBC, there, so the stick can
# be tried at once. A club is brought across with Club > Export club and File > Import club.
# The release workflow (.github/workflows/release.yml) runs this; make_stick.sh is the way to
# make a stick with your own clubs.

set -euo pipefail
cd "$(dirname "$0")"

if [ $# -ne 2 ]; then
    sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
fi
folder="${1%/}"
version="$2"
linux="$folder/lakemark-$version-linux"
windows="$folder/lakemark-$version-windows.exe"
zip="lakemark-$version-stick.zip"
for file in "$linux" "$windows"; do
    [ -f "$file" ] || { echo "No $file" >&2; exit 1; }
done

stick="$(mktemp -d)"
trap 'rm -rf "$stick"' EXIT
mkdir -p "$stick/LakeMark/output" "$stick/LakeMark/system"
cp "$linux" "$stick/LakeMark/lakemark"
cp "$windows" "$stick/LakeMark/lakemark.exe"
chmod +x "$stick/LakeMark/lakemark"
cp portable/install-windows.bat "$stick/LakeMark/"
cp portable/README.txt portable/start-linux.sh "$stick/LakeMark/system/"
cp "portable/LakeMark quick-start.pdf" "$stick/"

rm -f "$folder/$zip"
out="$(cd "$folder" && pwd)/$zip"
(cd "$stick" && zip -qr -9 "$out" "LakeMark quick-start.pdf" LakeMark)
echo "Made $folder/$zip"
