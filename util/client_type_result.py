import asyncio
import platform

import clipman
import keyboard

from util.config import ClientConfig as Config


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
        else:
            try:
                if keyboard.is_pressed(Config.offline_translate_shortcut):
                    keyboard.release(Config.offline_translate_shortcut)
                if keyboard.is_pressed(Config.online_translate_shortcut):
                    keyboard.release(Config.online_translate_shortcut)
                keyboard.send("ctrl + v")
                print("模拟粘贴2",Config.paste)
            except Exception as e:
                print(f"Windows/Linux粘贴操作失败: {e}")
                # 降级到直接写入方式
                keyboard.write(text)
                print("降级使用直接写入方式")

        # 还原剪贴板
        print("还原剪贴板",temp)
        if Config.restore_clipboard_after_paste:
            await asyncio.sleep(0.1)
            clipman.set(temp)

    # 模拟打印
    else:
        print("模拟打印",text)
        keyboard.write(text)
