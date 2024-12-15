from pathlib import Path
from unittest import result
import ctypes
import win32gui

from config import ClientConfig as Config


def encode_booleans(*args):
    result = 0
    for i, arg in enumerate(args):
        if arg:
            result |= (1 << i)
    return result

# def send_signal(hwnd, message, WPARAM, LPARAM):
#     result = win32gui.SendMessage(hwnd, message, WPARAM, LPARAM)
#     if result == 0:
#         # print("Message sent successfully.")
#         return True
#     else:
#         # print(f"Failed to send message, error code: {result}")
#         return result

# 必须使用 PostMessage 的方法, 不然在需要双击的情况下，不能继续执行下一行代码
# SendMessage: 是同步的。这意味着它会在消息处理完成后才返回。这可以导致调用线程阻塞，直到消息被目标窗口处理完毕。
# PostMessage: 是异步的。它会立即返回，而不等待目标窗口处理消息。这避免了调用线程的阻塞。
def send_signal(hwnd, message, WPARAM, LPARAM):
    try:
        # print("Before SendMessage")
        result = win32gui.PostMessage(hwnd, message, WPARAM, LPARAM)
        # print("After SendMessage, result:", result)
        if result:
            # print("Message posted successfully.")
            return True
        else:
            # print(f"Failed to post message, error code: {result}")
            return result
    except Exception as e:
        # print("Exception in send_signal:", e)
        return None


def send_signal_to_hint_while_recording(is_microphone_in_use: bool, is_short_duration: bool, offline_translate: bool, online_translate: bool, hold_mode: bool):
    exe_path = Path().cwd() / "hint_while_recording.exe"
    hwnd = win32gui.FindWindow(
        "AutoHotkey",
        str(exe_path),
    )
    if hwnd:
        # print("Found window, handle is:", hwnd)
        encoded_bools = encode_booleans(is_microphone_in_use, is_short_duration, offline_translate, online_translate, hold_mode)
        result = send_signal(hwnd, 0x5555, encoded_bools, 0)
    else:
        # print("Window not found")
        result = "Window not found"
    return result


def list_all_window():
    title = win32gui.GetWindowText(hwnd)
    className = win32gui.GetClassName(hwnd)
    print(f"Hwnd: {hwnd}, Title: {title}, Class: {className}")
    return True


if __name__ == "__main__":
    # win32gui.EnumWindows(list_all_window, 0)
    result = send_signal_to_hint_while_recording(True, Config.hold_mode)
    print(result)
