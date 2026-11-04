# iina-auto-hdr

Your Mac turns HDR on when an HDR movie plays in [IINA](https://iina.io), and back off when it stops.

macOS doesn't switch HDR per video like an Apple TV does. Leave HDR on for an external monitor and the desktop looks washed out; leave it off and HDR movies lose their highlights. iina-auto-hdr watches IINA and flips the switch for you:

- **HDR video starts** (HDR10, HLG or Dolby Vision): HDR turns on for your HDR-capable external display(s), and brightness goes to max if you use [BetterDisplay](https://github.com/waydabber/BetterDisplay).
- **Video stops or IINA closes:** HDR turns off and brightness goes back to what it was.
- **SDR video:** nothing changes.

It checks the video itself (its transfer curve), not the file name.

## Requirements

- macOS on Apple Silicon (tested on macOS 27.0.1, M2 Pro). Intel Macs should work but are untested.
- An external display with HDR support (the "High Dynamic Range" switch shows in System Settings > Displays).
- [IINA](https://iina.io) (tested with 1.5.0).
- Xcode Command Line Tools (`xcode-select --install`), to build the small HDR switch.
- Optional: BetterDisplay, for max brightness during HDR. Without it, brightness is left alone.

## Install

Quit IINA first, then:

```bash
git clone https://github.com/dylanbuchi/iina-auto-hdr.git
cd iina-auto-hdr
./install.sh
```

The installer:
1. adds one option to IINA (Settings > Advanced > Additional mpv options): `input-ipc-server=/tmp/mpvsocket`, so the watcher can ask IINA what it's playing. It also turns on IINA's advanced settings, which that option needs;
2. builds `hdr` and copies everything to `~/Library/Application Support/iina-auto-hdr`;
3. starts the watcher now and at every login. Log: `~/Library/Logs/iina-auto-hdr.log`.

You can also switch HDR by hand: `~/Library/Application\ Support/iina-auto-hdr/hdr on` (or `off`, `toggle`, `status`).

## Uninstall

Quit IINA, then:

```bash
./uninstall.sh
```

## Settings

Set these in the LaunchAgent (`~/Library/LaunchAgents/io.github.dylanbuchi.iina-auto-hdr.plist`, `EnvironmentVariables`) if you need them:

| Variable | Default | What it does |
|---|---|---|
| `AUTOHDR_MAX_BRIGHTNESS` | `1` | `0` leaves brightness alone |
| `AUTOHDR_POLL` | `5` | seconds between checks |
| `AUTOHDR_SOCKET` | `/tmp/mpvsocket` | IINA's mpv socket |

## Limits

- IINA only for now. Other players (Infuse, VLC, browsers) aren't detected.
- The HDR switch uses a private macOS function (the same one System Settings uses). A future macOS update could break it.
- Some monitors change their own picture settings (sharpness, picture mode) when HDR turns on or off. That happens inside the monitor and iina-auto-hdr can't undo it.
- The built-in MacBook screen is left alone; it handles HDR by itself.

## Support

iina-auto-hdr is free and open source. If it makes your movie nights better, you can buy me a coffee; it helps me keep it working after macOS updates.

<a href="https://ko-fi.com/dylanbuchi"><img src="https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?logo=ko-fi&logoColor=white" alt="Buy me a coffee on Ko-fi"></a>

## License

MIT
