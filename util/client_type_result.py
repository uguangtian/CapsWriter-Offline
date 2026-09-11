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


async def type_result(text):
    # 模拟粘贴
    print("模拟粘贴",Config.paste)
    if Config.paste:
        # 保存剪切板
        try:
            # 初始化剪贴板模块
            clipman.init()
            temp = clipman.get()
        except clipman.exceptions.ClipmanBaseException as e:
            temp = e
            print(e)

        # 复制结果
        print("模拟粘贴 text:",text)
        clipman.set(text)

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
            mode = (getattr(Config, "linux_paste_mode", None) or "ctrl_v").lower()
            try:
                if mode == "type":
                    await asyncio.to_thread(_linux_pynput_type, text)
                    print("Linux 输出完成 (pynput 逐字输入，适合 SSH/tmux)")
                elif mode in ("ctrl_shift_v", "shift", "terminal"):
                    await asyncio.to_thread(_linux_pynput_paste, True)
                    print("Linux 粘贴操作完成 (Ctrl+Shift+V，适合本地终端)")
                else:
                    await asyncio.to_thread(_linux_pynput_paste, False)
                    print("Linux 粘贴操作完成 (Ctrl+V，适合本地 GUI 编辑器)")
            except Exception as e:
                print(f"Linux 输出失败: {e}")
                try:
                    await asyncio.to_thread(_linux_pynput_type, text)
                    print("降级使用 pynput 直接输入")
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

        # 还原剪贴板
        print("还原剪贴板",temp)
        if Config.restore_clipboard_after_paste:
            await asyncio.sleep(0.1)
            clipman.set(temp)

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
