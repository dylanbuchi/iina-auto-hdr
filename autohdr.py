#!/usr/bin/env python3
"""iina-auto-hdr: turn macOS HDR on (and brightness up) while IINA plays an HDR video, restore after.

IINA must expose mpv's control socket (install.sh sets `input-ipc-server` in IINA).
Brightness uses BetterDisplay's command line if it's installed; otherwise it's skipped.
"""
import json, os, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
HDR = os.path.join(HERE, "hdr")
SOCK = os.environ.get("AUTOHDR_SOCKET", "/tmp/mpvsocket")
STOP_DELAY = float(os.environ.get("AUTOHDR_STOP_DELAY", "2"))  # seconds without HDR video before restoring
MAX_BRIGHTNESS = os.environ.get("AUTOHDR_MAX_BRIGHTNESS", "1") == "1"
BD = "/Applications/BetterDisplay.app/Contents/MacOS/BetterDisplay"

def log(*a):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)

def is_hdr(vp):
    if not vp:
        return False
    gamma = vp.get("gamma") or vp.get("transfer")
    return gamma in ("pq", "hlg") or "dolby" in str(vp.get("colormatrix", "")).lower()

class Iina:
    """Stays connected to IINA's mpv socket; IINA tells us right away when the video changes."""
    def __init__(self):
        self.sock, self.buf, self.hdr = None, b"", False

    def _connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(SOCK)
            s.sendall(b'{"command": ["observe_property", 1, "video-params"]}\n')
        except OSError:
            s.close()
            return False
        self.sock, self.buf = s, b""
        return True

    def _drop(self):
        if self.sock:
            self.sock.close()
        self.sock, self.hdr = None, False

    def wait(self, timeout=1.0):
        """Wait up to `timeout` s for news from IINA. Returns True while an HDR video is loaded."""
        if self.sock is None and not self._connect():
            time.sleep(timeout)  # IINA not open yet
            return False
        self.sock.settimeout(timeout)
        try:
            chunk = self.sock.recv(65536)
        except socket.timeout:
            return self.hdr
        except OSError:
            chunk = b""
        if not chunk:  # IINA quit
            self._drop()
            return False
        self.buf += chunk
        *lines, self.buf = self.buf.split(b"\n")
        for line in lines:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get("event") == "property-change" and m.get("name") == "video-params":
                self.hdr = is_hdr(m.get("data"))
        return self.hdr

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
    iina, last_hdr = Iina(), time.monotonic()
    while True:
        if iina.wait():
            last_hdr = time.monotonic()
            if state is None:
                state = turn_on()
        elif state is not None and time.monotonic() - last_hdr >= STOP_DELAY:
            # short wait so a quick glitch (or the switch to the next episode) doesn't end HDR
            restore(state)
            state = None

if __name__ == "__main__":
    main()
