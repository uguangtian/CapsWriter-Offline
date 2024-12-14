from pathlib import Path
from unittest import result

import win32gui

from config import ClientConfig as Config


def send_signal(hwnd, message, WPARAM, LPARAM):
    result = win32gui.SendMessage(hwnd, message, WPARAM, LPARAM)
    if result == 0:
        # print("Message sent successfully.")
        return True
    else:
        # print(f"Failed to send message, error code: {result}")
        return result


def send_signal_to_hint_while_recording(is_microphone_in_use: bool, hold_mode: bool):
    exe_path = Path().cwd() / "hint_while_recording.exe"
    hwnd = win32gui.FindWindow(
        "AutoHotkey",
        str(exe_path),
    )
    if hwnd:
        # print("Found window, handle is:", hwnd)
        result = send_signal(hwnd, 0x5555, is_microphone_in_use, hold_mode)
    else:
        # print("Window not found")
        result = "Window not found"
    return result


def list_all_window():
    title = win32gui.GetWindowText(hwnd)
    className = win32gui.GetClassName(hwnd)
    # print(f"Hwnd: {hwnd}, Title: {title}, Class: {className}")
    return True


if __name__ == "__main__":
    # win32gui.EnumWindows(list_all_window, 0)
    result = send_signal_to_hint_while_recording(True, Config.hold_mode)
    print(result)
