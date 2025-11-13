#!/bin/bash

# 创建一个在终端中启动 CapsWriter 的 AppleScript 应用

APP_NAME="CapsWriter-Offline-Terminal"
APP_PATH="./dist/${APP_NAME}.app"
SCRIPT_PATH="$(pwd)"

# 删除已存在的应用
if [ -d "$APP_PATH" ]; then
    rm -rf "$APP_PATH"
fi

# 创建应用目录结构
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 创建 Info.plist
cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>CapsWriter-Offline-Terminal</string>
    <key>CFBundleIdentifier</key>
    <string>com.capswriter.offline.terminal</string>
    <key>CFBundleName</key>
    <string>CapsWriter-Offline-Terminal</string>
    <key>CFBundleDisplayName</key>
    <string>CapsWriter离线版(终端)</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>CapsWriter需要访问麦克风进行语音识别</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>CapsWriter需要发送Apple Events来控制其他应用程序</string>
    <key>NSSystemAdministrationUsageDescription</key>
    <string>CapsWriter需要系统管理权限来监控键盘输入</string>
</dict>
</plist>
EOF

# 创建启动脚本
cat > "$APP_PATH/Contents/MacOS/CapsWriter-Offline-Terminal" << 'EOF'
#!/bin/bash

# 获取应用包的路径
APP_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
PROJECT_DIR="/Users/liu/data/python/CapsWriter-Offline"

# 在新的终端窗口中启动应用
osascript -e "tell application \"Terminal\" to do script \"cd \\\"$PROJECT_DIR\\\" && bash \\\"$PROJECT_DIR/launch_in_terminal.sh\\\"\""
EOF

# 设置执行权限
chmod +x "$APP_PATH/Contents/MacOS/CapsWriter-Offline-Terminal"

echo "✓ 终端应用已创建: $APP_PATH"
echo "现在可以双击启动应用，它会在终端中运行"