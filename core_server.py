import asyncio
import os
import sys
import atexit
from multiprocessing import Manager, Process
from platform import system
import json

import websockets

from util.config import ServerConfig as Config
from util.config import DeepSeekConfig
from util.config import get_config_dict
from util.empty_working_set import empty_current_working_set
from util.server_check_model import check_model
from util.server_cosmic import Cosmic, console
from util.server_init_recognizer import init_recognizer
from util.server_ws_recv import ws_recv
from util.server_ws_send import ws_send
from util.server_android_connection import start_android_connection_service

# 存储所有需要清理的进程
processes = []

def cleanup_processes():
    """清理所有子进程"""
    console.print("\n[yellow]正在清理进程...[/yellow]")
    for p in processes:
        if p.is_alive():
            p.terminate()
            p.join(timeout=1)
    console.print("[green]进程清理完成[/green]")

def run_chat_ui():
    """运行chat ui服务"""
    try:
        from agent.model_services.chat_ui import app
        app.run(host='0.0.0.0', port=5001)
    except Exception as e:
        console.print(f"[red]Chat UI 服务启动失败: {str(e)}[/red]")

# 注册退出时的清理函数
atexit.register(cleanup_processes)

# 确保 os.getcwd() 位置正确，用相对路径加载模型
BASE_DIR = os.getcwd()
os.chdir(BASE_DIR)
# BASE_DIR = os.path.dirname(__file__); os.chdir(BASE_DIR)


async def main():
    # 检查模型文件
    check_model()

    console.line(2)
    console.rule("[bold #d55252]CapsWriter Offline Server")
    console.line()
    console.print(
        "项目地址：[cyan underline]https://github.com/HaujetZhao/CapsWriter-Offline",
        end="\n\n",
    )
    console.print(f"当前基文件夹：[cyan underline]{BASE_DIR}", end="\n\n")
    console.print(
        f"绑定的服务地址：[cyan underline]{Config.addr}:{Config.speech_recognition_port}",
        end="\n\n",
    )

    console.print("载入模块中，载入时长约 50 秒，请耐心等待...")

    # 跨进程列表，用于保存 socket 的 id，用于让识别进程查看连接是否中断
    Cosmic.sockets_id = Manager().list()
    console.print(f"[DEBUG] 初始化 recognizer 进程..., socket_id:{Cosmic.sockets_id}", style="cyan")

    # 负责识别的子进程
    recognize_process = Process(
        target=init_recognizer,
        args=(Cosmic.queue_in, Cosmic.queue_out, Cosmic.sockets_id, get_config_dict()),
        daemon=True,
    )
    recognize_process.start()
    processes.append(recognize_process)
    Cosmic.queue_out.get()

    # 启动离线翻译 WebSocket服务器
    if Config.start_offline_translate_server:
        console.print("载入离线翻译模型中，载入时长约 20 秒，请耐心等待...")
        from util.server_run_offline_translate_service import (
            run_offline_translate_service,
        )

        translate_offline_server_process = Process(target=run_offline_translate_service)
        translate_offline_server_process.start()
        processes.append(translate_offline_server_process)

    # 启动在线翻译 DeepLX服务器
    if Config.start_online_translate_server:
        console.print("启动在线翻译 DeepLX 服务...")
        from util.server_run_online_translate_service import (
            run_online_translate_service,
        )

        run_online_translate_service()
        
    # 启动DeepSeek API服务
    # if DeepSeekConfig.start_deepseek_server:
    #     console.print("启动DeepSeek API服务...")
    #     from util.server_run_deepseek_service import (
    #         run_deepseek_service,
    #     )

    #     deepseek_server_process = Process(target=run_deepseek_service)
    #     deepseek_server_process.start()
    #     processes.append(deepseek_server_process)
    
    # 启动Android连接服务
    # console.print("启动Android连接服务...")
    # discovery_thread = start_android_connection_service()

    # 启动 chat_ui.py 服务
    console.print("启动 Chat UI 服务...")
    chat_ui_process = Process(
        target=run_chat_ui,
        daemon=True
    )
    chat_ui_process.start()
    processes.append(chat_ui_process)
    console.print("[green]Chat UI 服务已启动在 http://localhost:5001")

    console.rule("[green3]开始服务")
    console.line()

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    # 负责接收客户端数据的 coroutine
    console.print("[green]websocket 服务即将启动 ",Config.addr,":",Config.speech_recognition_port)


    try:
        # 负责接收客户端数据的 WebSocket 服务器
        async with websockets.serve(
            ws_recv,
            Config.addr,
            Config.speech_recognition_port,
            subprotocols=None,  # 移除子协议要求
            max_size=None,
        ) as recv_server:
            console.print("[green]websocket 服务已启动在 ",Config.addr,":",Config.speech_recognition_port)
            
            # 负责发送结果的 coroutine
            send = ws_send()
            
            # 同时运行接收和发送服务
            await asyncio.gather(asyncio.Future(), send)  # 使用Future()保持服务器运行
        
    except Exception as e:
        console.print(f"[red]websocket 服务启动失败: {str(e)}[/red]")
        return


def init():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # Ctrl-C 停止
        console.print("\n再见！")
    except OSError as e:  # 端口占用
        console.print(f"出错了：{e}", style="bright_red")
        console.input("...")
    except Exception as e:
        print(e)
    finally:
        Cosmic.queue_out.put(None)
        cleanup_processes()  # 确保在退出前清理进程
        sys.exit(0)
        # os._exit(0)


if __name__ == "__main__":
    init()
