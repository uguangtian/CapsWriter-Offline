#!/bin/bash

# CapsWriter-Offline macOS 开机自启动设置脚本
# 这个脚本会创建 LaunchAgent 配置文件，实现开机自启动

set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# LaunchAgents 目录
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.capswriter.offline.plist"

echo "=== CapsWriter-Offline 开机自启动设置 ==="
echo "项目目录: $PROJECT_DIR"
echo "LaunchAgent 文件: $PLIST_FILE"
echo

# 创建 LaunchAgents 目录（如果不存在）
if [ ! -d "$LAUNCH_AGENTS_DIR" ]; then
    echo "创建 LaunchAgents 目录..."
    mkdir -p "$LAUNCH_AGENTS_DIR"
fi

# 创建 plist 文件
echo "创建 LaunchAgent 配置文件..."
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.capswriter.offline</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>Terminal</string>
        <string>$PROJECT_DIR/launch_in_terminal.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/CapsWriter-Offline.log</string>
    
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/CapsWriter-Offline-error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "✓ LaunchAgent 配置文件已创建"

# 加载 LaunchAgent
echo "加载 LaunchAgent..."
launchctl load "$PLIST_FILE"
echo "✓ LaunchAgent 已加载"

echo
echo "=== 开机自启动设置完成 ==="
echo "CapsWriter-Offline 现在会在用户登录时自动启动"
echo
echo "管理命令:"
echo "  查看状态: launchctl list | grep com.capswriter.offline"
echo "  停止服务: launchctl unload \"$PLIST_FILE\""
echo "  启动服务: launchctl load \"$PLIST_FILE\""
echo "  删除自启动: rm \"$PLIST_FILE\" && launchctl unload \"$PLIST_FILE\""
echo
echo "日志文件:"
echo "  标准输出: $HOME/Library/Logs/CapsWriter-Offline.log"
echo "  错误输出: $HOME/Library/Logs/CapsWriter-Offline-error.log"
echo