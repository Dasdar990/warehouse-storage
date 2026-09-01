# NFC badge bridge (MIKROE-2540 / PN7150)

The USB dongle used for badge login is not a keyboard-wedge reader — it's
driven by NXP's precompiled `NXP-NCI_Linux_example` binary, which just
prints tag events to its own stdout. A browser tab can't read a process's
stdout directly, so this script bridges the two: it runs the NXP binary,
parses each line, and re-broadcasts badge taps as JSON over a local
WebSocket that the login page listens on.

```
dongle USB --(NCI/HID)--> NXP binary --(stdout)--> bridge.py --(WebSocket)--> login page
```

The bridge never talks to the backend API itself — it only tells the
browser "this badge was tapped." The browser then calls
`POST /auth/badge-login` exactly as it already does for a keyboard-wedge
badge reader (see `frontend/composables/useAuth.ts`).

## Requirements

- Linux, with `stdbuf` available (part of `coreutils`, present on virtually
  every distro).
- The precompiled NXP binary for the PN7150 (from `SW4335.zip` on NXP's
  PN7150 / MIKROE-2540 product page), or a binary built from NXP's source
  with `make` (requires `libhidapi-dev`).
- Python 3.9+

## Setup

```bash
cd nfc-bridge
pip install -r requirements.txt
```

## Running

```bash
python3 bridge.py /path/to/nxp-nci-demo
```

Optional flags:

```bash
python3 bridge.py /path/to/nxp-nci-demo --ws-host 127.0.0.1 --ws-port 8765
```

The bridge must run on the **same machine as the browser** showing the
login page — normally the kiosk the dongle is physically plugged into —
because the WebSocket defaults to `127.0.0.1`. It's independent of where
the backend API is hosted; the frontend's `NUXT_PUBLIC_NFC_BRIDGE_URL` env
var (default `ws://localhost:8765`) is separate from `NUXT_PUBLIC_API_BASE`.

If you get "Attenzione: 'stdbuf' non trovato" the process still runs, but
output may arrive in bursts rather than line-by-line.

## First-time UID format check

Before relying on it in production, run the NXP binary by hand once, tap a
badge, and check the printed line matches what `bridge.py` expects:

```
NFCID = e6 52 83 82
```

The bridge's regex also accepts `UID = ...` and `NFCID1 = ...`, since the
exact label can vary by NXP package version. If your output looks
different, adjust `UID_PATTERN` in `bridge.py`.

## WebSocket message format

```jsonc
{"type": "badge_tap", "uid": "E6528382"}     // badge read (normalized: uppercase, no separators)
{"type": "badge_removed"}                     // badge lifted away
{"type": "reader_status", "status": "waiting"} // back to polling for a tag
```

The login page only acts on `badge_tap`; the other two are there for future
UI feedback (e.g. "remove badge" / "waiting for badge" states) and can be
ignored by any client that doesn't need them.

## Running as a background service

Since this needs to run continuously on the kiosk, consider a systemd unit:

```ini
[Unit]
Description=NFC badge bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/warehouse-storage/nfc-bridge/bridge.py /opt/nxp/nxp-nci-demo
Restart=always
User=kiosk

[Install]
WantedBy=multi-user.target
```
