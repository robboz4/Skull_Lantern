#!/bin/bash
# Installs the skull animation as a boot-time service on the lantern's Pi.
#
# Usage:  sudo bash install_skull_service.sh <skull_rot_ccw.raw|skull_rot_cw.raw> [fps]
# Run it from the folder that contains play_skull.py and the .raw files.
set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run with sudo."
  exit 1
fi

RAW="${1:-}"
FPS="${2:-12}"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST=/opt/skull-lantern

if [ -z "$RAW" ] || [ ! -f "$SRC/$RAW" ]; then
  echo "Usage: sudo bash $0 <skull_rot_ccw.raw|skull_rot_cw.raw> [fps]"
  echo "Looked for the .raw file in: $SRC"
  exit 1
fi
if [ ! -f "$SRC/play_skull.py" ]; then
  echo "play_skull.py not found in $SRC"
  exit 1
fi

mkdir -p "$DEST"
cp "$SRC/play_skull.py" "$DEST/play_skull.py"
cp "$SRC/$RAW" "$DEST/skull.raw"

# Launcher: waits for the TFT framebuffer to appear, then plays the animation
cat > "$DEST/run.sh" <<'EOF'
#!/bin/sh
i=0
while [ ! -e /dev/fb1 ] && [ "$i" -lt 60 ]; do
  sleep 1
  i=$((i + 1))
done
exec /usr/bin/python3 /opt/skull-lantern/play_skull.py /opt/skull-lantern/skull.raw "${FPS:-12}"
EOF
chmod 755 "$DEST/run.sh"

cat > /etc/systemd/system/skull-lantern.service <<EOF
[Unit]
Description=Pepper's Ghost skull animation
After=multi-user.target

[Service]
Type=simple
Environment=FPS=$FPS
ExecStart=$DEST/run.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now skull-lantern.service

echo
echo "Installed. The skull should now be playing, and will start automatically at every boot."
systemctl --no-pager status skull-lantern.service | head -n 8
