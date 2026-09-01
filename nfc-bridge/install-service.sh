#!/usr/bin/env bash
# Installs the NFC bridge as a systemd service, so it starts automatically
# on boot and restarts itself if it ever crashes -- nobody has to remember
# to run "python3 bridge.py ..." by hand again.
#
# Usage (from inside nfc-bridge/):
#   sudo ./install-service.sh [path/to/NXP-NCI_Linux]
#
# If the binary path is omitted, it defaults to ./NXP-NCI_Linux (the
# prebuilt binary already sitting in this folder).

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this with sudo (it installs a systemd service): sudo ./install-service.sh"
  exit 1
fi

BRIDGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BINARY_PATH="${1:-$BRIDGE_DIR/NXP-NCI_Linux}"
# Runs as root by default: USB HID devices are usually root-owned unless
# you've set up a specific udev rule granting a group access to this
# dongle's vendor/product id, and getting that rule exactly right isn't
# worth guessing at here. If you'd rather not run it as root, add a udev
# rule for the dongle and change User=root below to your own user before
# re-running this script.
RUN_AS_USER="root"
SERVICE_NAME="warehouse-nfc-bridge"
VENV_DIR="$BRIDGE_DIR/.venv"

if [ ! -f "$BINARY_PATH" ]; then
  echo "Error: NXP binary not found at $BINARY_PATH"
  echo "Pass its path explicitly: sudo ./install-service.sh /path/to/NXP-NCI_Linux"
  exit 1
fi
chmod +x "$BINARY_PATH"

if ! command -v stdbuf >/dev/null 2>&1; then
  echo "Error: 'stdbuf' not found (part of coreutils). Install it first, e.g.:"
  echo "  sudo apt install coreutils"
  exit 1
fi

echo "Bridge folder:   $BRIDGE_DIR"
echo "NXP binary:      $BINARY_PATH"
echo "Runs as user:    $RUN_AS_USER"

# Isolated virtualenv so the bridge's one dependency (websockets) never
# collides with anything else on the machine.
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv..."
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install -q -r "$BRIDGE_DIR/requirements.txt"

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Warehouse Storage NFC badge bridge (PN7150 / MIKROE-2540)
After=network.target

[Service]
ExecStart=$VENV_DIR/bin/python3 $BRIDGE_DIR/bridge.py $BINARY_PATH
WorkingDirectory=$BRIDGE_DIR
Restart=always
RestartSec=2
User=$RUN_AS_USER

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo
echo "Done. The bridge now starts automatically on boot and restarts itself if it crashes."
echo
echo "Useful commands:"
echo "  systemctl status ${SERVICE_NAME}     # is it running?"
echo "  journalctl -u ${SERVICE_NAME} -f     # live logs (badge taps show up here)"
echo "  sudo systemctl restart ${SERVICE_NAME}"
