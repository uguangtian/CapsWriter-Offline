#!/bin/bash
# Ubuntu：user systemd 常驻 core_server + core_client（需已配置 config.toml 与 models）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_PY="$PROJECT_DIR/.venv/bin/python3"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

if [[ ! -x "$VENV_PY" ]]; then
  echo "缺少 $VENV_PY，请先: python3 -m venv .venv && pip install -r requirements-linux-voice.txt"
  exit 1
fi
if [[ ! -f "$PROJECT_DIR/config.toml" ]]; then
  echo "缺少 config.toml，可先: cp config_example.toml config.toml"
  exit 1
fi

mkdir -p "$UNIT_DIR"

# 图形会话：本机实测为 X11 + DISPLAY :1（/tmp/.X11-unix/X1）；:0 无效
CAPSWRITER_DISPLAY="${CAPSWRITER_DISPLAY:-}"
if [[ -z "$CAPSWRITER_DISPLAY" ]]; then
  if [[ -S /tmp/.X11-unix/X1 ]]; then
    CAPSWRITER_DISPLAY=":1"
  elif [[ -S /tmp/.X11-unix/X0 ]]; then
    CAPSWRITER_DISPLAY=":0"
  else
    CAPSWRITER_DISPLAY=":0"
  fi
fi
if [[ -f /run/user/$(id -u)/gdm/Xauthority ]]; then
  CAPSWRITER_XAUTH="/run/user/$(id -u)/gdm/Xauthority"
else
  CAPSWRITER_XAUTH="${HOME}/.Xauthority"
fi

cat > "$UNIT_DIR/capswriter-server.service" <<EOF
[Unit]
Description=CapsWriter Offline ASR server
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONUNBUFFERED=1
ExecStart=${VENV_PY} ${PROJECT_DIR}/core_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

cat > "$UNIT_DIR/capswriter-client.service" <<EOF
[Unit]
Description=CapsWriter Offline client (mic + shortcut)
After=network-online.target sound.target capswriter-server.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=DISPLAY=${CAPSWRITER_DISPLAY}
Environment=XAUTHORITY=${CAPSWRITER_XAUTH}
ExecStart=${VENV_PY} ${PROJECT_DIR}/core_client.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable capswriter-server.service capswriter-client.service
echo "已安装 user systemd 单元。启动: systemctl --user start capswriter-server capswriter-client"
echo "日志: journalctl --user -u capswriter-client -f"
