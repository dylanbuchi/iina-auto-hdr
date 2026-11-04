#!/bin/bash
# Removes iina-auto-hdr and turns HDR back off.
cd "$(dirname "$0")"
DEST="$HOME/Library/Application Support/iina-auto-hdr"
LABEL="io.github.dylanbuchi.iina-auto-hdr"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
[ -x "$DEST/hdr" ] && "$DEST/hdr" off >/dev/null
/usr/bin/python3 iina_config.py remove || echo "Quit IINA and run uninstall.sh again to remove its setting."
rm -rf "$DEST"
echo "Removed."
