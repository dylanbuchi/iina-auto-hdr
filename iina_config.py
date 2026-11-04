#!/usr/bin/env python3
"""Add or remove IINA's mpv option `input-ipc-server=/tmp/mpvsocket` (IINA must be closed)."""
import os, plistlib, subprocess, sys

DOMAIN = "com.colliderli.iina"
KEY, VALUE = "input-ipc-server", "/tmp/mpvsocket"

def main(action):
    if subprocess.run(["pgrep", "-x", "IINA"], capture_output=True).returncode == 0:
        print("Please quit IINA first, then run this again."); sys.exit(1)
    raw = subprocess.run(["defaults", "export", DOMAIN, "-"], capture_output=True).stdout
    prefs = plistlib.loads(raw) if raw else {}
    if raw:  # keep a copy of IINA's settings, just in case
        backup = os.path.expanduser("~/Library/Application Support/iina-auto-hdr/iina-prefs-backup.plist")
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        with open(backup, "wb") as f:
            f.write(raw)
    opts = [o for o in prefs.get("userOptions", []) if not (len(o) == 2 and o[0] == KEY)]
    if action == "add":
        opts.append([KEY, VALUE])
        prefs["enableAdvancedSettings"] = True
    prefs["userOptions"] = opts
    subprocess.run(["defaults", "import", DOMAIN, "-"], input=plistlib.dumps(prefs), check=True)
    print(f"IINA: {KEY} {'added' if action == 'add' else 'removed'}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "add")
