#!/bin/bash

# CapsWriter-Offline macOS 开机自启动移除脚本
# 这个脚本会移除 LaunchAgent 配置文件，取消开机自启动

set -e

# LaunchAgents 目录和文件
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.capswriter.offline.plist"

echo "=== CapsWriter-Offline 开机自启动移除 ==="
echo "LaunchAgent 文件: $PLIST_FILE"
echo

# 检查文件是否存在
if [ ! -f "$PLIST_FILE" ]; then
    echo "❌ LaunchAgent 配置文件不存在，可能未设置开机自启动"
    echo "文件路径: $PLIST_FILE"
    exit 1
fi

# 卸载 LaunchAgent
echo "卸载 LaunchAgent..."
launchctl unload "$PLIST_FILE" 2>/dev/null || echo "LaunchAgent 可能已经卸载"
echo "✓ LaunchAgent 已卸载"

# 删除配置文件
echo "删除配置文件..."
rm "$PLIST_FILE"
echo "✓ 配置文件已删除"

echo
echo "=== 开机自启动移除完成 ==="
echo "CapsWriter-Offline 不再会在用户登录时自动启动"
echo
echo "如需重新设置开机自启动，请运行: ./create_autostart.sh"
echo