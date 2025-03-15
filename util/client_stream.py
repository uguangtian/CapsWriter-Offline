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
        Cosmic.queue_in.put( #将音频放入队列
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

    # 从配置中获取麦克风设备索引或名称
    device_index = Config.microphone_device_index
    device_name = Config.microphone_device_name
    devices = sd.query_devices()
    # 打印所有可用的音频设备序号和名字
    console.print("可用的音频设备：")
    for i, device in enumerate(devices):
        # 只显示输入设备
        if device["max_input_channels"] > 0:
            console.print(f"  {i}: {device['name']}")
             
        
    # 如果配置了设备索引，则优先使用索引
    if device_index is not None:
        try:
            device_info = sd.query_devices(device_index, kind="input")
            device_name = device_info["name"]
            channels = min(2, device_info["max_input_channels"])
            console.print(
                f"使用配置的音频设备（索引 {device_index}）：[italic]{device_name}，声道数：{channels}", end="\n\n"
            )
        except ValueError:
            console.print(f"[red]无效的设备索引：{device_index}[/red]")
            sys.exit()
    # 如果配置了设备名称，则尝试匹配设备名称
    elif device_name:
        devices = sd.query_devices()
        matching_devices = [d for d in devices if device_name in d["name"]]
        if matching_devices:
            device_info = matching_devices[0]
            device_index = device_info["index"]
            channels = min(2, device_info["max_input_channels"])
            console.print(
                f"使用配置的音频设备（名称包含 {device_name}）：[italic]{device_info['name']}，声道数：{channels}", end="\n\n"
            )
        else:
            console.print(f"[red]未找到匹配的设备名称：{device_name}[/red]")
            sys.exit()
    else:
        # 如果没有配置，则使用默认设备
        try:
            device_info = sd.query_devices(kind="input")
            device_name = device_info["name"]
            if channels is None:
                channels = min(2, device_info["max_input_channels"])
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

    # 打开音频流
    if Config.only_enable_microphones_when_pressed_record_shortcut:
        stream = sd.InputStream(
            samplerate=48000,
            blocksize=int(0.05 * 48000),  # 0.05 seconds
            device=device_index,
            dtype="float32",
            channels=channels,
            callback=record_callback,  # 放入音频的回调
        )  # stream.start()
    else:
        stream = sd.InputStream(
            samplerate=48000,
            blocksize=int(0.05 * 48000),  # 0.05 seconds
            device=device_index,
            dtype="float32",
            channels=channels,
            callback=record_callback,
            finished_callback=stream_reopen,
        )
        stream.start()

    return stream
