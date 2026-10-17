#!/usr/bin/env bash
# ==============================================================================
# Android Cast - macOS Application Launcher
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES="$DIR/../Resources"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
export PYTHONPATH="$RESOURCES:$PYTHONPATH"
export SCRCPY_ICON_DIR="$RESOURCES"

if [ -f "$RESOURCES/scrcpy-server" ]; then
    export SCRCPY_SERVER_PATH="$RESOURCES/scrcpy-server"
fi

exec /usr/bin/python3 "$RESOURCES/src/main.py" "$@"

