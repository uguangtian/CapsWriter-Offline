# 调用 everything 搜索光标选中的字符

# .\runtime\python.exe .\util\client_search_selected_text_with_everything.py


import asyncio

import clipman
import keyboard

from util.client_cosmic import console
from util.config import ClientConfig as Config


async def on_hotkey_pressed():
    try:
        # 复制选中的文本
        if keyboard.is_pressed("ctrl"):
            keyboard.release("ctrl")
        if keyboard.is_pressed("alt"):
            keyboard.release("alt")
        keyboard.send("ctrl + c")
        await asyncio.sleep(0.1)  # 等待剪贴板更新
        # 保存剪切板
        try:
            # 初始化剪贴板模块
            clipman.init()
            temp = clipman.get()
        except clipman.exceptions.ClipmanBaseException as e:
            temp = e
            console.print(e)
        text = temp
        # 控制台输出
        console.print(f"选中文本：{text}")
        # 打开 everything
        await asyncio.create_subprocess_exec(
            Config.everything_exe_path, "-search", text
        )
    except Exception as e:
        console.print(e)


def hotkey_callback():
    asyncio.run_coroutine_threadsafe(on_hotkey_pressed(), loop)


async def search_selected_text_with_everything():
    try:
        # 获取事件循环
        global loop
        loop = asyncio.get_event_loop()

        # 注册热键
        keyboard.add_hotkey(
            Config.search_selected_text_with_everything_shortcut, hotkey_callback
        )

        await asyncio.Event().wait()  # 阻塞当前协程，直到被取消或热键被触发
    except Exception as e:
        console.print(e)
    finally:
        keyboard.remove_hotkey(
            Config.search_selected_text_with_everything_shortcut
        )  # 移除热键


if __name__ == "__main__":
    asyncio.run(search_selected_text_with_everything())
