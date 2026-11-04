#!/usr/bin/env python3
"""iina-auto-hdr: turn macOS HDR on (and brightness up) while IINA plays an HDR video, restore after.

IINA must expose mpv's control socket (install.sh sets `input-ipc-server` in IINA).
Brightness uses BetterDisplay's command line if it's installed; otherwise it's skipped.
"""
import json, os, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
HDR = os.path.join(HERE, "hdr")
SOCK = os.environ.get("AUTOHDR_SOCKET", "/tmp/mpvsocket")
POLL = float(os.environ.get("AUTOHDR_POLL", "5"))
MAX_BRIGHTNESS = os.environ.get("AUTOHDR_MAX_BRIGHTNESS", "1") == "1"
BD = "/Applications/BetterDisplay.app/Contents/MacOS/BetterDisplay"

def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)

def mpv_get(prop):
    """Ask IINA (mpv) for one property. None if nothing is playing or IINA isn't open."""
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(SOCK)
        s.sendall((json.dumps({"command": ["get_property", prop], "request_id": 7}) + "\n").encode())
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                return None
            buf += chunk
            for line in buf.split(b"\n"):
                try:
                    m = json.loads(line)
                except ValueError:
                    continue
                if m.get("request_id") == 7:
                    return m.get("data")
    except OSError:
        return None
    finally:
        s.close()

def playing_hdr():
    vp = mpv_get("video-params")
    if not vp:
        return False
    gamma = vp.get("gamma") or vp.get("transfer")
    return gamma in ("pq", "hlg") or "dolby" in str(vp.get("colormatrix", "")).lower()

def hdr(cmd):
    """Run the HDR switch; returns the display IDs it handled."""
    out = subprocess.run([HDR, cmd], capture_output=True, text=True).stdout
    return [line.split()[0] for line in out.splitlines() if line.strip()]

def bd_brightness(display_id, value=None):
    if not (MAX_BRIGHTNESS and os.path.exists(BD)):
        return None
    if value is None:
        out = subprocess.run([BD, "get", f"-displayID={display_id}", "-brightness"], capture_output=True, text=True).stdout
        try:
            return float(out.strip())
        except ValueError:
            return None
    subprocess.run([BD, "set", f"-displayID={display_id}", f"-brightness={value}"], capture_output=True)

def main():
    if not os.path.exists(HDR):
        log("missing hdr tool next to autohdr.py, run install.sh"); sys.exit(1)
    log("started; brightness", "via BetterDisplay" if MAX_BRIGHTNESS and os.path.exists(BD) else "unchanged")
    active, saved = False, {}
    while True:
        want = playing_hdr()
        if want and not active:
            ids = hdr("on")
            saved = {i: bd_brightness(i) for i in ids}
            for i in ids:
                bd_brightness(i, 1)
            active = True
            log("HDR video: HDR on for displays", ids, "brightness was", saved)
        elif not want and active:
            hdr("off")
            for i, v in saved.items():
                if v is not None:
                    bd_brightness(i, v)
            active = False
            log("back to normal")
        time.sleep(POLL)

if __name__ == "__main__":
    main()
