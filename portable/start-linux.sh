#!/usr/bin/env bash
# Start the portable copy's program, for when it will not run straight from the USB stick
# (a stick mounted "noexec", or one that has lost the file's permission to run).
#
#     bash Lakemark/system/start-linux.sh
#
# Runs ../lakemark if it can; otherwise runs a copy from a temporary folder, with this
# system folder as its data folder, and removes the copy when it closes.

set -u
system="$(cd "$(dirname "$0")" && pwd)"
program="$(dirname "$system")/lakemark"

if [ ! -f "$program" ]; then
    echo "Cannot find the program: $program" >&2
    exit 1
fi

if "$program" --version >/dev/null 2>&1; then
    exec "$program" --data "$system" "$@"
fi

copy="$(mktemp -d)"
trap 'rm -rf "$copy"' EXIT
cp "$program" "$copy/lakemark"
chmod +x "$copy/lakemark"
"$copy/lakemark" --data "$system" "$@"
