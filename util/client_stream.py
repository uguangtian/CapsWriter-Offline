import asyncio
import sys
import threading
import time

import numpy as np
import sounddevice as sd

from util.client_cosmic import Cosmic, console
from util.config import ClientConfig as Config
from platform import system


def record_callback(
    indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags
) -> None:
    if not Cosmic.on:
        return
    asyncio.run_coroutine_threadsafe(
        Cosmic.queue_in.put(
            {
                "type": "data",
                "time": time.time(),
                "data": indata.copy(),
            },
        ),
        Cosmic.loop,
    )


def stream_close(signum, frame):
    # Mac上无法退出
    print("system():",system())
    if system() == 'darwin':
        return

    Cosmic.stream.close()


def stream_reopen():
    if not threading.main_thread().is_alive():
        return
    print("重启音频流")

    # 关闭旧流
    Cosmic.stream.close()

    # 重载 PortAudio，更新设备列表
    sd._terminate()
    sd._ffi.dlclose(sd._lib)
    sd._lib = sd._ffi.dlopen(sd._libname)
    sd._initialize()

    # 打开新流
    time.sleep(0.1)
    Cosmic.stream = stream_open()


def stream_open():
    # 显示录音所用的音频设备
        # 添加 Mac 特定的权限检查
    if sys.platform == 'darwin':
        try:
            # 尝试初始化一个临时流来触发系统权限请求
            temp_stream = sd.InputStream(samplerate=48000, channels=1)
            temp_stream.start()
            temp_stream.stop()
            temp_stream.close()
        except sd.PortAudioError as e:
            console.print(f"[red]无法访问麦克风：{e}[/red]")
            console.print("[yellow]请在系统偏好设置中授予麦克风访问权限[/yellow]")
            input("按回车键退出")
            sys.exit()
    channels = 1
    try:
        device = sd.query_devices(kind="input")
        device_name = device["name"]
        channels = min(2, device["max_input_channels"])
        console.print(
            f"使用默认音频设备：[italic]{device_name}，声道数：{channels}", end="\n\n"
        )
    except UnicodeDecodeError:
        console.print(
            "由于编码问题，暂时无法获得麦克风设备名字", end="\n\n", style="bright_red"
        )
    except sd.PortAudioError:
        console.print("没有找到麦克风设备", end="\n\n", style="bright_red")
        input("按回车键退出")
        sys.exit()

    if Config.only_enable_microphones_when_pressed_record_shortcut:
        stream = sd.InputStream(
            samplerate=48000,
            blocksize=int(0.05 * 48000),  # 0.05 seconds
            device=None,
            dtype="float32",
            channels=channels,
            callback=record_callback,
            # finished_callback=stream_reopen,
        )  # stream.start()
    else:
        stream = sd.InputStream(
            samplerate=48000,
            blocksize=int(0.05 * 48000),  # 0.05 seconds
            device=None,
            dtype="float32",
            channels=channels,
            callback=record_callback,
            finished_callback=stream_reopen,
        )
        stream.start()

    return stream
