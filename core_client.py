# coding: utf-8

print("程序开始执行", flush=True)  # 添加这一行作为最早的调试输出

import asyncio
import os
import signal
import sys
import pdb
import argparse
import gc
import base64

print("导入基本模块完成", flush=True)

from pathlib import Path
from platform import system
from typing import List

import colorama
import typer

print("导入第三方模块完成", flush=True)

from util.client_cosmic import Cosmic, console
from util.client_show_tips import show_file_tips, show_mic_tips
from util.client_hot_update import observe_hot, update_hot_all
from util.client_stream import stream_close, stream_open
from util.client_shortcut_handler import bond_shortcut

from util.config import ClientConfig as Config
from util.client_recv_result import recv_result
from util.client_adjust_srt import adjust_srt
from util.empty_working_set import empty_current_working_set
# if sys.argv[1:]:
#     Cosmic.transcribe_subtitles = True
# else:
#     Cosmic.transcribe_subtitles = False
# from util.client_adjust_srt import adjust_srt
# print("在 MacOS 上需要以管理员启动客户端才能监听键盘活动，请 sudo 启动")


from util.client_transcribe import transcribe_check, transcribe_recv, transcribe_send
# from util.empty_working_set import empty_current_working_set

# 确保根目录位置正确，用相对路径加载模型
BASE_DIR = os.getcwd()
print(f"当前工作目录: {BASE_DIR}", flush=True)
os.chdir(BASE_DIR)
# BASE_DIR = os.path.dirname(__file__); os.chdir(BASE_DIR)

# 确保终端能使用 ANSI 控制字符
colorama.init()
print("初始化 colorama 完成", flush=True)

# MacOS 的权限设置
if system() == "Darwin" and not sys.argv[1:]:
    print("检查 MacOS 权限...", flush=True)
    try:
        # 使用 ctypes 直接调用 ApplicationServices 框架
        import ctypes
        
        # 加载 ApplicationServices 框架
        framework = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        
        # 定义函数原型
        framework.AXIsProcessTrusted.restype = ctypes.c_bool
        
        # 检查是否有辅助功能权限
        trusted = framework.AXIsProcessTrusted()
        print(f"辅助功能权限检查结果: {trusted}", flush=True)
        if not trusted:
            print("请在系统偏好设置 -> 安全性与隐私 -> 隐私 -> 辅助功能中授予权限")
            print("授权后重新启动程序")
            input("按回车退出")
            sys.exit()
    except Exception as e:
        print(f"检查辅助功能权限时出错: {e}", flush=True)
        print("请先安装必要的包：")
        print("pip install pyobjc")
        input("按回车退出")
        sys.exit()
    if False:
        # 仍然需要管理员权限的检查
        print("检查管理员权限...", flush=True)
        if os.getuid() != 0: #获取用户 ID
            print("在 MacOS 上需要以管理员启动客户端才能监听键盘活动，请 sudo 启动")
            input("按回车退出")
            sys.exit()
        else:
            os.umask(0o000)
            print("管理员权限检查通过", flush=True)

print("权限检查完成", flush=True)

# 定义信号处理函数
def signal_handler(signum, frame):
    console.print("\n[yellow]signal_handler 接收到退出信号，正在关闭...[/yellow]")
    sys.exit(0)

    if Cosmic.stream:
        print("关闭音频流")
        stream_close(signum, frame)
    if Cosmic.websocket:
        print("关闭 websocket")
        # asyncio.create_task(Cosmic.websocket.close())
    sys.exit(0)

async def main_mic():
    
    Cosmic.loop = asyncio.get_event_loop()
    Cosmic.queue_in = asyncio.Queue()
    Cosmic.queue_out = asyncio.Queue()

    show_mic_tips()

    # 更新热词
    update_hot_all()

    # 实时更新热词
    observer = observe_hot()

    # 初始化内存监控
    try:
        from util.memory_monitor import start_memory_monitoring, cleanup_memory
        # 启动内存监控，设置阈值为70%，每60秒检查一次
        start_memory_monitoring(threshold_percent=70.0, check_interval=60)
        print("内存监控已启动")
        # 初始执行一次内存清理
        cleanup_memory()
    except ImportError:
        print("内存监控模块未找到，跳过内存监控初始化")
        
    # 打开音频流
    Cosmic.stream = stream_open()
    
    # Ctrl-C 关闭音频流，触发自动重启
    # signal.signal(signal.SIGINT, stream_close)

    signal.signal(signal.SIGINT, signal_handler)


    # 绑定按键
    print("绑定按键")
    bond_shortcut()

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    # 接收结果
    print(
        f"连接服务端...  （服务端载入模块时长约 50 秒，请耐心等待。若好几分钟了还无响应 -> 服务端软件 start_server_gui.exe 启动了吗？ 服务端地址当前设置 {Config.addr}:{Config.speech_recognition_port} 是正确的吗？）"
    )
    # await recv_result()
    while True:
        await recv_result()


async def main_file(files: List[Path]):
    print("main_file")
    """
    pdb.set_trace() 是 Python 内置的一个调试工具，用于在代码的特定位置设置一个断点。当程序运行到这行代码时，会暂停执行，并进入交互式调试模式。通过这个调试模式，你可以检查变量的值、单步执行代码、调用函数等，从而帮助你诊断和修复代码中的问题。

    ### PDB 的基本用法
    1. 设置断点 ：将 pdb.set_trace() 插入到你想暂停执行的地方。
    2. 启动程序 ：正常运行程序，当执行到 pdb.set_trace() 时，程序会暂停。
    3. 调试命令 ：
    - n (next)：执行下一行代码。
    - c (continue)：继续执行直到遇到下一个断点。
    - l (list)：显示当前代码上下文。
    - p <variable> ：打印变量的值。
    - q (quit)：退出调试并终止程序。
    如果你不再需要调试，可以直接删除或注释掉 pdb.set_trace() 这一行代码：
    """

    # pdb.set_trace()
    show_file_tips()
    
    # 初始化内存监控
    try:
        from util.memory_monitor import start_memory_monitoring, cleanup_memory
        # 启动内存监控，设置阈值为70%，每60秒检查一次
        start_memory_monitoring(threshold_percent=70.0, check_interval=60)
        print("内存监控已启动")
        # 初始执行一次内存清理
        cleanup_memory()
        memory_monitor_available = True
    except ImportError:
        print("内存监控模块未找到，跳过内存监控初始化")
        memory_monitor_available = False

    # 统计处理文件数量，用于内存管理
    total_files = len(files)
    processed_count = 0
    
    for file in files:
        processed_count += 1
        
        if file.suffix in [".txt", ".json", ".srt"]:
            # 检查是否已经处理过这些文本文件
            processed_file = file.with_suffix('.processed')
            if processed_file.exists():
                print(f"文本文件 {file} 已处理过，跳过")
                continue
            
            adjust_srt(file)
            
            # 可选：标记为已处理
            # with open(processed_file, 'w') as f:
            #     f.write('processed')
        else:
            # 检查是否已存在对应的 SRT 文件
            srt_file = file.with_suffix('.srt')
            if srt_file.exists():
                print(f"文件 {file} 已有对应的字幕文件 {srt_file}，跳过转录")
                continue
                
            print(f"正在转录文件 {file} ({processed_count}/{total_files})")
            await transcribe_check(file)
            await asyncio.gather(transcribe_send(file), transcribe_recv(file))
            
            # 每处理完一个文件执行一次内存清理
            if memory_monitor_available:
                print("执行内存清理...")
                await asyncio.to_thread(cleanup_memory)
                
            # 强制执行垃圾回收
            gc.collect()

    if Cosmic.websocket:
        await Cosmic.websocket.close()
    input("\n按回车退出\n")


def init_mic():
    print("初始化麦克风")

    try:
        asyncio.run(main_mic())
    except KeyboardInterrupt:
        console.print("再见！")
    finally:
        print("...")


def init_file(files: List[Path]):
    """
    用 CapsWriter Server 转录音视频文件，生成 srt 字幕
    """
    try:
        asyncio.run(main_file(files))
    except KeyboardInterrupt:
        console.print("再见！")
        sys.exit()


if __name__ == "__main__":
    print("进入主函数", flush=True)

    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description="CapsWriter 客户端")
    parser.add_argument("--channels", type=int, default=None, help="指定录音的声道数 (1 或 2)")
    parser.add_argument("--device", type=int, default=None, help="指定录音设备的索引")
    parser.add_argument("--device-name", type=str, default=None, help="指定录音设备的名称（支持部分匹配）")
    parser.add_argument("--file", type=str, default=None, help="指定文件（目录）")
    parser.add_argument("--url", type=str, default=None, help="视频网址")
    
    print("解析命令行参数...", flush=True)
    args = parser.parse_args()
    print(f"命令行参数: {args}", flush=True)
    
    print("开始执行主逻辑", flush=True)
    
    # 下载地址中的视频
    if args.url is not None:
        print(f"准备下载视频: {args.url}", flush=True)
        from download_video import download_and_transcribe
        print("已导入 download_and_transcribe 函数", flush=True)
        
        try:
            print("开始执行下载...", flush=True)
            # 使用 asyncio.run 运行异步函数，但添加错误处理
            asyncio.run(download_and_transcribe(args.url, output_dir="/Users/anker/Movies/CapsWriter"))
        except KeyboardInterrupt:
            print("\n下载被用户中断", flush=True)
        except Exception as e:
            print(f"\n下载过程中出错: {e}", flush=True)
        finally:
            print("下载处理完成", flush=True)
        
        print("下载流程结束，退出程序", flush=True)
        sys.exit(0)
    
    # 如果参数传入文件，那就转录文件
    # 如果没有多余参数，就从麦克风输入
    if args.file is not None:      
        # 检查输入是否为文件夹
        input_paths = [Path(p) for p in sys.argv[1:]]
        # typer.run(init_file)
    
        file_paths = []
        
        for path in input_paths:
            if path.is_dir():
                # 如果是文件夹，遍历处理其中的所有视频和音频文件
                print(f"处理文件夹: {path}")
                # 定义支持的视频和音频文件扩展名
                media_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv',  # 视频
                                   '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']  # 音频
                
                # 遍历文件夹中的所有文件
                for file in path.glob('**/*'):
                    if file.is_file() and file.suffix.lower() in media_extensions:
                        print(f"找到媒体文件: {file}")
                        file_paths.append(file)
            else:
                # 如果是文件，直接添加
                file_paths.append(path)
        
        if file_paths:
            # 使用找到的所有文件路径调用 init_file
            # 不直接调用 init_file，而是通过 typer.run 执行
            asyncio.run(main_file(file_paths))
        else:
            print("未找到任何媒体文件")
            sys.exit(1)
    else:
              # 如果命令行指定了设备索引或名称，更新配置
        print(f"按键模式: {Config.hold_mode}")
        if args.device is not None:
            Config.microphone_device_index = args.device
        if args.device_name is not None:
            Config.microphone_device_name = args.device_name
        init_mic()

