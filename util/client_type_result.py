import asyncio
import platform

import clipman
import keyboard

from util.config import ClientConfig as Config


def _linux_pynput_paste(use_shift: bool = False):
    from pynput.keyboard import Controller, Key

    controller = Controller()
    if use_shift:
        with controller.pressed(Key.ctrl, Key.shift):
            controller.press("v")
            controller.release("v")
    else:
        with controller.pressed(Key.ctrl):
            controller.press("v")
            controller.release("v")


def _linux_pynput_type(text: str):
    from pynput.keyboard import Controller

    Controller().type(text)


def _linux_paste_mode() -> str:
    return (getattr(Config, "linux_paste_mode", None) or "auto").lower()


def _linux_inject_via_keyboard_only(mode: str) -> bool:
    """终端 / tmux / SSH：只按键注入，不写剪贴板，避免「先贴再敲」重复一遍。"""
    return mode in ("type", "auto", "terminal", "tty")


def _linux_uses_clipboard_shortcut(mode: str) -> bool:
    return mode in ("ctrl_v", "gui", "ctrl_shift_v", "shift", "terminal_paste")


async def type_result(text):
    # 模拟粘贴
    print("模拟粘贴",Config.paste)
    if Config.paste:
        linux_mode = _linux_paste_mode() if platform.system() == "Linux" else None
        use_clipboard = not (
            platform.system() == "Linux" and _linux_inject_via_keyboard_only(linux_mode)
        )

        temp = None
        if use_clipboard:
            try:
                clipman.init()
                temp = clipman.get()
            except clipman.exceptions.ClipmanBaseException as e:
                temp = e
                print(e)
            print("模拟粘贴 text:", text)
            clipman.set(text)
        else:
            print("模拟输出 text:", text)

        # 粘贴结果
        if platform.system() == "Darwin":  # Mac
            try:
                # 使用异步方式在Mac上模拟粘贴
                process = await asyncio.create_subprocess_exec(
                    'osascript', '-e', 
                    'tell application "System Events" to keystroke "v" using command down',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
                if process.returncode == 0:
                    print("Mac粘贴操作完成")
                else:
                    print(f"Mac粘贴操作失败，返回码: {process.returncode}, 错误: {stderr.decode()}")
                    # 降级到直接写入方式
                    keyboard.write(text)
                    print("降级使用直接写入方式")
            except (asyncio.TimeoutError, Exception) as e:
                print(f"Mac粘贴操作异常: {e}")
                # 降级到直接写入方式
                keyboard.write(text)
                print("降级使用直接写入方式")
        elif platform.system() == "Linux":
            mode = linux_mode
            try:
                if _linux_inject_via_keyboard_only(mode):
                    await asyncio.to_thread(_linux_pynput_type, text)
                    print(
                        "Linux 输出完成 (逐字键入；plain shell / tmux / SSH 通用，不碰剪贴板)"
                    )
                elif mode in ("ctrl_shift_v", "shift", "terminal_paste"):
                    await asyncio.to_thread(_linux_pynput_paste, True)
                    print("Linux 粘贴完成 (Ctrl+Shift+V，仅一次)")
                else:
                    await asyncio.to_thread(_linux_pynput_paste, False)
                    print("Linux 粘贴完成 (Ctrl+V，本地 GUI 编辑器)")
            except Exception as e:
                print(f"Linux 输出失败: {e}")
                if _linux_uses_clipboard_shortcut(mode):
                    try:
                        await asyncio.to_thread(_linux_pynput_type, text)
                        print("降级：逐字键入（避免重复请勿再手动粘贴）")
                    except Exception as e2:
                        print(f"Linux 直接输入失败: {e2}")
        else:
            try:
                if keyboard.is_pressed(Config.offline_translate_shortcut):
                    keyboard.release(Config.offline_translate_shortcut)
                if keyboard.is_pressed(Config.online_translate_shortcut):
                    keyboard.release(Config.online_translate_shortcut)
                keyboard.send("ctrl + v")
                print("模拟粘贴2", Config.paste)
            except Exception as e:
                print(f"Windows 粘贴操作失败: {e}")
                keyboard.write(text)
                print("降级使用直接写入方式")

        if use_clipboard:
            print("还原剪贴板", temp)
            if Config.restore_clipboard_after_paste and temp is not None:
                await asyncio.sleep(0.1)
                try:
                    clipman.set(temp)
                except clipman.exceptions.ClipmanBaseException as e:
                    print(e)

    # 模拟打印
    else:
        print("模拟打印", text)
        if platform.system() == "Linux":
            try:
                await asyncio.to_thread(_linux_pynput_type, text)
            except Exception as e:
                print(f"Linux 直接输入失败: {e}")
        else:
            keyboard.write(text)
