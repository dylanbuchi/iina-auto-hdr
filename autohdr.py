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

def hdr(cmd, ids=()):
    """Run the HDR switch. Returns {displayID: "on"|"off"} for the displays it handled."""
    out = subprocess.run([HDR, cmd, *ids], capture_output=True, text=True).stdout
    return {p[0]: p[1] for p in (line.split() for line in out.splitlines()) if len(p) >= 2}

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

STATE = os.path.expanduser("~/Library/Application Support/iina-auto-hdr/state.json")

def save_state(state):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None

def turn_on():
    before = hdr("status")
    switched = [i for i, st in before.items() if st == "off"]  # leave displays the user already had in HDR alone
    brightness = {i: bd_brightness(i) for i in before}  # read before HDR changes it
    state = {"switched": switched, "brightness": brightness}
    save_state(state)  # so a restart mid-movie can still put things back
    if switched:
        hdr("on", switched)
    for i, v in brightness.items():
        if v is not None:
            bd_brightness(i, 1)
    log("HDR video: HDR on for displays", switched, "brightness was", brightness)
    return state

def restore(state):
    if state.get("switched"):
        hdr("off", state["switched"])
    for i, v in state.get("brightness", {}).items():
        if v is not None:
            bd_brightness(i, v)
    try:
        os.remove(STATE)
    except OSError:
        pass
    log("back to normal")

def main():
    if not os.path.exists(HDR):
        log("missing hdr tool next to autohdr.py, run install.sh")
        time.sleep(60)  # launchd restarts us; don't spam the log
        sys.exit(1)
    log("started; brightness", "via BetterDisplay" if MAX_BRIGHTNESS and os.path.exists(BD) else "unchanged")
    state = load_state()  # left over if we were stopped during an HDR video
    if state is not None and not playing_hdr():
        restore(state)
        state = None
    misses = 0
    while True:
        want = playing_hdr()
        misses = 0 if want else misses + 1
        if want and state is None:
            state = turn_on()
        elif misses >= 2 and state is not None:  # 2 checks in a row: one odd answer from IINA shouldn't end HDR mid-movie
            restore(state)
            state = None
        time.sleep(POLL)

if __name__ == "__main__":
    main()
