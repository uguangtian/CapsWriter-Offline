#!/bin/bash

# CapsWriter-Offline 统一启动器 (macOS/Linux Shell版本)
# 这个脚本提供了一键启动服务端和客户端的功能

set -e  # 遇到错误时退出

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
    echo "========================================"
    echo "   CapsWriter-Offline 统一启动器"
    echo "========================================"
    echo ""
    echo "使用方法:"
    echo "  ./start_unified.sh                    # 统一启动服务端和客户端"
    echo "  ./start_unified.sh --server-only      # 仅启动服务端"
    echo "  ./start_unified.sh --client-only      # 仅启动客户端"
    echo "  ./start_unified.sh --background       # 后台模式启动"
    echo "  ./start_unified.sh --help             # 显示帮助信息"
    echo ""
    echo "注意：首次运行可能需要执行 chmod +x start_unified.sh 来添加执行权限"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        if ! command -v python &> /dev/null; then
            print_error "未找到Python，请确保Python已正确安装"
            exit 1
        else
            PYTHON_CMD="python"
        fi
    else
        PYTHON_CMD="python3"
    fi
    
    print_success "找到Python: $(${PYTHON_CMD} --version)"
    
    # 检查必要文件
    if [ ! -f "start_unified.py" ]; then
        print_error "未找到 start_unified.py 文件"
        exit 1
    fi
    
    print_success "依赖检查完成"
}

# 清理函数
cleanup() {
    print_info "正在清理..."
    # 这里可以添加清理逻辑
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    # 解析命令行参数
    case "$1" in
        --help|-h)
            show_help
            exit 0
            ;;
        --version)
            echo "CapsWriter-Offline 统一启动器 v1.0"
            exit 0
            ;;
    esac
    
    echo "========================================"
    echo "   CapsWriter-Offline 统一启动器"
    echo "========================================"
    echo ""
    
    # 检查依赖
    check_dependencies
    
    print_info "正在启动 CapsWriter-Offline..."
    echo ""
    
    # 启动Python脚本
    ${PYTHON_CMD} start_unified.py "$@"
    
    # 检查退出代码
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "程序正常退出"
    else
        print_error "程序异常退出 (退出代码: $exit_code)"
        exit $exit_code
    fi
}

# 检查是否在正确的目录中
if [ ! -f "start_unified.py" ]; then
    print_error "请在 CapsWriter-Offline 项目根目录中运行此脚本"
    exit 1
fi

# 运行主函数
main "$@"