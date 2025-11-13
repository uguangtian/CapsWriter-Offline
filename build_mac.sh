#!/bin/bash

# CapsWriter-Offline Mac应用打包脚本
# 这是一个简化的shell脚本，用于快速打包Mac应用

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    echo "CapsWriter-Offline Mac应用打包脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --help          显示此帮助信息"
    echo "  --no-dmg       不创建DMG安装包"
    echo "  --version VER  指定应用版本号"
    echo ""
    echo "示例:"
    echo "  $0                    # 完整打包（包含DMG）"
    echo "  $0 --no-dmg          # 只生成.app文件"
    echo "  $0 --version 2.0.0   # 指定版本号"
    echo ""
}

# 处理帮助参数
for arg in "$@"; do
    if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
        show_help
        exit 0
    fi
done

# 检查是否在正确的目录
if [ ! -f "start_unified.py" ]; then
    print_error "请在CapsWriter-Offline项目根目录下运行此脚本"
    exit 1
fi

print_info "开始构建CapsWriter-Offline Mac应用..."
echo "================================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    print_error "Python3未安装或不在PATH中"
    exit 1
fi

print_success "Python3环境检查通过"

# 检查并安装PyInstaller
print_info "检查PyInstaller..."
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    print_warning "PyInstaller未安装，正在安装..."
    python3 -m pip install pyinstaller
    print_success "PyInstaller安装完成"
else
    print_success "PyInstaller已安装"
fi

# 运行Python打包脚本
print_info "执行打包脚本..."
python3 build_mac_app.py "$@"

# 检查打包结果
if [ -d "dist/CapsWriter-Offline.app" ]; then
    print_success "应用打包成功！"
    echo "================================================"
    print_info "应用位置: $(pwd)/dist/CapsWriter-Offline.app"
    
    if [ -f "dist/CapsWriter-Offline-1.0.0.dmg" ]; then
        print_info "DMG位置: $(pwd)/dist/CapsWriter-Offline-1.0.0.dmg"
    fi
    
    echo ""
    print_info "使用说明:"
    echo "  1. 双击 .app 文件即可运行应用"
    echo "  2. 首次运行可能需要在系统偏好设置中允许运行"
    echo "  3. 如果创建了DMG，可以分发DMG文件给其他用户"
    echo ""
    print_success "🎉 打包完成！"
else
    print_error "应用打包失败！"
    exit 1
fi