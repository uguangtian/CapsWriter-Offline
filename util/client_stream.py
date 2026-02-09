import asyncio
import sys
import threading
import time
import subprocess
import platform

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
        console.print("[yellow]主线程已退出，无法重启音频流[/yellow]")
        return
    console("重启音频流")

    # 关闭旧流
    console("重启音频流 关闭旧流")
    Cosmic.stream.close()

    # 重载 PortAudio，更新设备列表
    console("重启音频流 重载 PortAudio，更新设备列表")
    sd._terminate()
    sd._ffi.dlclose(sd._lib)
    sd._lib = sd._ffi.dlopen(sd._libname)
    sd._initialize()

    # 打开新流
    print("重启音频流 打开新流")
    time.sleep(0.1)
    Cosmic.stream = stream_open()


def get_macos_version():
    """获取macOS版本号"""
    try:
        version_str = platform.mac_ver()[0]
        major, minor = map(int, version_str.split('.')[:2])
        return major, minor
    except:
        return 10, 15  # 默认返回较老版本


def open_privacy_settings():
    """打开系统隐私设置"""
    try:
        major, minor = get_macos_version()
        if major >= 13:  # macOS Ventura 13.0+ 使用新的系统设置
            # 尝试新版系统设置URL
            subprocess.run(["open", "x-apple.systempreferences:com.apple.SystemPreferences.Extensions?Privacy_Microphone"], check=False)
            time.sleep(0.5)  # 给系统一点时间
            # 备用方案：直接打开隐私与安全性
            subprocess.run(["open", "/System/Applications/System Preferences.app"], check=False)
        else:  # 较老版本的macOS
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"], check=False)
        return True
    except Exception as e:
        console.print(f"[yellow]无法自动打开设置：{e}[/yellow]")
        return False


def check_microphone_permission():
    """检查并请求麦克风权限"""
    if sys.platform == 'darwin':
        console.print("[blue]正在检查麦克风权限...[/blue]")
        
        # 首先检查是否有可用的音频输入设备
        try:
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if not input_devices:
                console.print("[red]✗ 未检测到任何音频输入设备[/red]")
                console.print("[yellow]请确保已连接麦克风设备[/yellow]")
                return False
        except Exception as e:
            console.print(f"[yellow]警告：无法查询音频设备：{e}[/yellow]")
        
        try:
            # 尝试初始化一个临时流来触发系统权限请求
            temp_stream = sd.InputStream(samplerate=48000, channels=1, blocksize=1024)
            temp_stream.start()
            # 短暂录制以确保权限生效
            time.sleep(0.1)
            temp_stream.stop()
            temp_stream.close()
            console.print("[green]✓ 麦克风权限检查通过[/green]")
            return True
        except sd.PortAudioError as e:
            console.print(f"[red]✗ 无法访问麦克风：{e}[/red]")
            console.print("[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]")
            console.print("[yellow]🎤 需要授予麦克风访问权限[/yellow]")
            
            major, minor = get_macos_version()
            console.print(f"[dim]检测到 macOS {major}.{minor}[/dim]")
            
            console.print("[cyan]请按照以下步骤操作：[/cyan]")
            if major >= 13:  # macOS Ventura 13.0+
                console.print("[white]1. 打开 系统设置 > 隐私与安全性 > 麦克风[/white]")
            else:  # 较老版本的macOS
                console.print("[white]1. 打开 系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风[/white]")
            console.print("[white]2. 确保此应用程序已被勾选启用[/white]")
            console.print("[white]3. 如果没有看到此应用，请重启应用程序[/white]")
            console.print("[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]")
            
            # 提供选项
            while True:
                console.print("\n[cyan]请选择操作：[/cyan]")
                console.print("[white]  o - 自动打开隐私设置[/white]")
                console.print("[white]  r - 重新检查权限[/white]")
                console.print("[white]  q - 退出程序[/white]")
                
                choice = input("请输入选择 (o/r/q): ").lower().strip()
                
                if choice == 'o':
                    console.print("[blue]正在打开系统隐私设置...[/blue]")
                    if open_privacy_settings():
                        console.print("[green]已打开隐私设置，请授权后选择重新检查[/green]")
                    else:
                        console.print("[yellow]请手动打开系统设置进行授权[/yellow]")
                elif choice == 'r':
                    console.print("[blue]重新检查权限...[/blue]")
                    return check_microphone_permission()  # 递归重试
                elif choice == 'q':
                    console.print("[yellow]用户选择退出[/yellow]")
                    sys.exit()
                else:
                    console.print("[red]请输入有效选择 (o/r/q)[/red]")
        except Exception as e:
            console.print(f"[red]检查麦克风权限时发生未知错误：{e}[/red]")
            return False
    else:
        # 非macOS系统，直接返回True
        return True


def stream_open():
    # 检查麦克风权限
    if not check_microphone_permission():
        console.print("[red]麦克风权限检查失败，程序退出[/red]")
        sys.exit()
    
    # 显示录音所用的音频设备

    # 从配置中获取麦克风设备索引或名称
    device_index = Config.microphone_device_index
    device_name = Config.microphone_device_name
    devices = sd.query_devices()
    # 打印所有可用的音频设备序号和名字
    console.print("可用的音频设备：")
    for i, device in enumerate(devices):
        # 只显示输入设备
        # console.print(f"  {i}: {device['name']}")
        if device["max_input_channels"] > 0:
            console.print(f"  {i}: {device['name']}")
             
    if device_index == -1:
        # 如果没有配置，则使用默认设备
        try:
            device_info = sd.query_devices(kind="input")
            device_index= device_info["index"]
            device_name = device_info["name"]
            channels = min(2, device_info["max_input_channels"])
            console.print(
                f"使用默认音频设备：idx:{device_index},[italic]{device_name}，声道数：{channels}", end="\n\n"
            )
        except UnicodeDecodeError:
            console.print(
                "由于编码问题，暂时无法获得麦克风设备名字", end="\n\n", style="bright_red"
            )
        except sd.PortAudioError:
            console.print("没有找到麦克风设备", end="\n\n", style="bright_red")
            input("按回车键退出")
            sys.exit()
    else:
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


    # 打开音频流
    console.print("打开音频流")
    if Config.only_enable_microphones_when_pressed_record_shortcut:
        console.print("打开音频流 仅在按下记录快捷键时启用麦克风")
        stream = sd.InputStream(
            samplerate=48000,
            blocksize=int(0.05 * 48000),  # 0.05 seconds
            device=device_index,
            dtype="float32",
            channels=channels,
            callback=record_callback,  # 放入音频的回调
        )  # stream.start()
    else:
        console.print("打开音频流  always enabled")
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
