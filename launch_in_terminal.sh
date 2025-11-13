#!/bin/bash

# CapsWriter-Offline 终端启动脚本
# 这个脚本会在终端中启动应用

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 切换到应用目录
cd "$SCRIPT_DIR"

# 激活虚拟环境
echo "激活虚拟环境..."
source "$SCRIPT_DIR/python3/bin/activate"

# 启动应用
echo "正在启动 CapsWriter-Offline..."
python3 start_unified.py

# 保持终端打开
echo "按任意键退出..."
read -n 1