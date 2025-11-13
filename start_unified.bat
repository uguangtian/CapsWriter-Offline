@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM CapsWriter-Offline 统一启动器 (Windows批处理版本)
REM 这个脚本提供了一键启动服务端和客户端的功能

echo ========================================
echo   CapsWriter-Offline 统一启动器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请确保Python已正确安装并添加到PATH环境变量中
    pause
    exit /b 1
)

REM 检查必要文件是否存在
if not exist "start_unified.py" (
    echo 错误：未找到 start_unified.py 文件
    pause
    exit /b 1
)

REM 解析命令行参数
set "ARGS="
set "SHOW_HELP=0"

:parse_args
if "%~1"=="" goto :start_app
if "%~1"=="--help" set "SHOW_HELP=1"
if "%~1"=="-h" set "SHOW_HELP=1"
set "ARGS=%ARGS% %~1"
shift
goto :parse_args

:start_app
if "%SHOW_HELP%"=="1" (
    echo 使用方法:
    echo   start_unified.bat                    # 统一启动服务端和客户端
    echo   start_unified.bat --server-only      # 仅启动服务端
    echo   start_unified.bat --client-only      # 仅启动客户端
    echo   start_unified.bat --background       # 后台模式启动
    echo   start_unified.bat --help             # 显示帮助信息
    echo.
    pause
    exit /b 0
)

echo 正在启动 CapsWriter-Offline...
echo.

REM 启动Python脚本
python start_unified.py %ARGS%

REM 检查退出代码
if errorlevel 1 (
    echo.
    echo 启动失败，请检查错误信息
    pause
    exit /b 1
)

echo.
echo 程序已退出
pause