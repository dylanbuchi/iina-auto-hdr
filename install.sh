#!/bin/bash
# Installs iina-auto-hdr: builds the HDR switch, sets up IINA, starts the watcher now and at every login.
set -euo pipefail
cd "$(dirname "$0")"
DEST="$HOME/Library/Application Support/iina-auto-hdr"
LABEL="io.github.dylanbuchi.iina-auto-hdr"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/iina-auto-hdr.log"

command -v swiftc >/dev/null || { echo "Needs Xcode Command Line Tools: run  xcode-select --install"; exit 1; }
[ -d /Applications/IINA.app ] || echo "Note: IINA not found in /Applications. Install it from https://iina.io"

/usr/bin/python3 iina_config.py add
mkdir -p "$DEST" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
swiftc -O hdr.swift -o "$DEST/hdr"
cp autohdr.py iina_config.py "$DEST/"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$LABEL</string>
<key>ProgramArguments</key><array><string>/usr/bin/python3</string><string>-u</string><string>$DEST/autohdr.py</string></array>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardOutPath</key><string>$LOG</string>
<key>StandardErrorPath</key><string>$LOG</string>
</dict></plist>
PL
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed. Displays found:"; "$DEST/hdr" status || true
echo "Log: $LOG"
