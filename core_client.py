# coding: utf-8

import asyncio
import os
import signal
import sys
import pdb

from pathlib import Path
from platform import system
from typing import List

import colorama
import typer

from util.client_cosmic import Cosmic, console
from util.client_show_tips import show_file_tips, show_mic_tips
from util.client_hot_update import observe_hot, update_hot_all
from util.client_stream import stream_close, stream_open
from util.client_shortcut_handler import bond_shortcut

from util.config import ClientConfig as Config
from util.client_recv_result import recv_result

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
os.chdir(BASE_DIR)
# BASE_DIR = os.path.dirname(__file__); os.chdir(BASE_DIR)

# 确保终端能使用 ANSI 控制字符
colorama.init()

# MacOS 的权限设置
if system() == "Darwin" and not sys.argv[1:]:
    try:
        # 使用 ctypes 直接调用 ApplicationServices 框架
        import ctypes
        
        # 加载 ApplicationServices 框架
        framework = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        
        # 定义函数原型
        framework.AXIsProcessTrusted.restype = ctypes.c_bool
        
        # 检查是否有辅助功能权限
        trusted = framework.AXIsProcessTrusted()
        if not trusted:
            print("请在系统偏好设置 -> 安全性与隐私 -> 隐私 -> 辅助功能中授予权限")
            print("授权后重新启动程序")
            input("按回车退出")
            sys.exit()
    except Exception as e:
        print(f"检查辅助功能权限时出错: {e}")
        print("请先安装必要的包：")
        print("pip install pyobjc")
        input("按回车退出")
        sys.exit()

            # 仍然需要管理员权限的检查
        if os.getuid() != 0:
            print("在 MacOS 上需要以管理员启动客户端才能监听键盘活动，请 sudo 启动")
            input("按回车退出")
            sys.exit()
        else:
            os.umask(0o000)


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

    # 打开音频流
    Cosmic.stream = stream_open()

    # Ctrl-C 关闭音频流，触发自动重启
    # signal.signal(signal.SIGINT, stream_close)

    signal.signal(signal.SIGINT, signal_handler)


    # 绑定按键
    bond_shortcut()

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    # 接收结果
    print(
        f"连接服务端...  （服务端载入模块时长约 50 秒，请耐心等待。若好几分钟了还无响应 -> 服务端软件 start_server_gui.exe 启动了吗？ 服务端地址当前设置 {Config.addr}:{Config.speech_recognition_port} 是正确的吗？）"
    )
    await recv_result()
    # while True:
    #     await recv_result()


async def main_file(files: List[Path]):
    print("main_file")

    pdb.set_trace()
    show_file_tips()

    for file in files:
        if file.suffix in [".txt", ".json", "srt"]:
            adjust_srt(file)
        else:
            print(f"正在转录文件 {file}")
            await transcribe_check(file)
            await asyncio.gather(transcribe_send(file), transcribe_recv(file))

    if Cosmic.websocket:
        await Cosmic.websocket.close()
    input("\n按回车退出\n")


def init_mic():
    print("init_mic")

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
    # 如果参数传入文件，那就转录文件
    # 如果没有多余参数，就从麦克风输入
    if sys.argv[1:]:
        print("typer.run", sys.argv[1:])
        
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

            # for file_path in file_paths:
            #     print(f"处理文件: {file_path}")
            #     # typer.run(init_file([file_path]))
            #     asyncio.run(main_file(file_path))

                # typer.run(lambda f=file_path: init_file([f]))
        else:
            print("未找到任何媒体文件")
        #     sys.exit(1)
    else:
        init_mic()
