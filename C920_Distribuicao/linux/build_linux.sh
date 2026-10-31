#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v dpkg-deb >/dev/null; then echo 'Instale dpkg-dev'; exit 1; fi
python3 -m venv .build-venv
.build-venv/bin/python -m pip install --upgrade pip
.build-venv/bin/python -m pip install -r requirements-build.txt
.build-venv/bin/python -m PyInstaller --noconfirm --clean --onedir --windowed --name c920-led-control \
  --add-data 'c920_led_gui.py:.' \
  --add-data 'windows/c920_led_controle_v10.py:windows' \
  --add-data 'linux/c920_led_linux.py:linux' \
  --paths . packaging/launcher.py
mkdir -p release
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/DEBIAN" "$STAGE/opt/c920-led-control" "$STAGE/usr/bin" "$STAGE/usr/share/applications"
cp -a dist/c920-led-control/. "$STAGE/opt/c920-led-control/"
cat > "$STAGE/usr/bin/c920-led-control" <<'EOF'
#!/bin/sh
exec /opt/c920-led-control/c920-led-control "$@"
EOF
chmod 755 "$STAGE/usr/bin/c920-led-control"
cat > "$STAGE/usr/share/applications/c920-led-control.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Logitech C920 LED Control
Comment=Controle do LED da webcam Logitech C920
Exec=/usr/bin/c920-led-control
Icon=camera-web
Terminal=false
Categories=Utility;Video;
EOF
ARCH="$(dpkg --print-architecture)"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: c920-led-control
Version: 0.4.0
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Logitech C920 LED Control community <noreply@example.invalid>
Depends: libc6, libstdc++6, libglib2.0-0 | libglib2.0-0t64, libx11-6, libxcb1, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libdbus-1-3
Description: Controle do LED da Logitech C920 (GUI Qt)
 Aplicativo com botoes ON automatico, OFF e BLINKING.
EOF
dpkg-deb --build --root-owner-group "$STAGE" "release/c920-led-control_0.4.0_${ARCH}.deb"
echo "Pacote criado em release/c920-led-control_0.4.0_${ARCH}.deb"
