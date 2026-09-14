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


def _linux_paste_mode() -> str:
    return (getattr(Config, "linux_paste_mode", None) or "auto").lower()


def _linux_paste_use_shift(mode: str) -> bool:
    # auto / 终端 / tmux：Ctrl+Shift+V；GUI 用 ctrl_v
    if mode in ("ctrl_v", "gui"):
        return False
    return mode in (
        "auto",
        "ctrl_shift_v",
        "shift",
        "terminal_paste",
        "terminal",
        "tty",
        "type",
    )


async def type_result(text):
    # 模拟粘贴
    print("模拟粘贴", Config.paste)
    if Config.paste:
        temp = None
        try:
            clipman.init()
            temp = clipman.get()
        except clipman.exceptions.ClipmanBaseException as e:
            temp = e
            print(e)

        print("模拟粘贴 text:", text)
        clipman.set(text)

        if platform.system() == "Darwin":
            try:
                process = await asyncio.create_subprocess_exec(
                    "osascript",
                    "-e",
                    'tell application "System Events" to keystroke "v" using command down',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
                if process.returncode == 0:
                    print("Mac粘贴操作完成")
                else:
                    print(
                        f"Mac粘贴操作失败，返回码: {process.returncode}, 错误: {stderr.decode()}"
                    )
                    keyboard.write(text)
                    print("降级使用直接写入方式")
            except (asyncio.TimeoutError, Exception) as e:
                print(f"Mac粘贴操作异常: {e}")
                keyboard.write(text)
                print("降级使用直接写入方式")
        elif platform.system() == "Linux":
            mode = _linux_paste_mode()
            try:
                if _linux_paste_use_shift(mode):
                    await asyncio.to_thread(_linux_pynput_paste, True)
                    print("Linux 粘贴完成 (Ctrl+Shift+V)")
                else:
                    await asyncio.to_thread(_linux_pynput_paste, False)
                    print("Linux 粘贴完成 (Ctrl+V)")
            except Exception as e:
                print(f"Linux 粘贴失败: {e}")
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

        print("还原剪贴板", temp)
        if Config.restore_clipboard_after_paste and temp is not None:
            await asyncio.sleep(0.1)
            try:
                clipman.set(temp)
            except clipman.exceptions.ClipmanBaseException as e:
                print(e)

    else:
        print("模拟打印", text)
        if platform.system() != "Linux":
            keyboard.write(text)
