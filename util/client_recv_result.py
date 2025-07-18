import json

import opencc
import websockets

import asyncio
# from util.server_run_deepseek_service import call_deepseek_api
# from util.server_run_doubao_service import call_doubao_api

from util.client_check_websocket import check_websocket
from util.client_cosmic import Cosmic, console
from util.client_hot_sub import hot_sub
from util.client_rename_audio import rename_audio
from util.client_strip_punc import strip_punc
from util.client_type_result import type_result
from util.client_write_md import write_md
from util.config import ClientConfig as Config

if not Cosmic.transcribe_subtitles:
    from util.client_translate_offline import translate_offline
    from util.client_translate_online import translate_online
import warnings

warnings.filterwarnings("ignore")


async def recv_result():
    # 添加重试机制
    max_retries = 3
    retry_count = 0
    retry_delay = 5  # 秒
    
    while retry_count < max_retries:
        if not await check_websocket():
            retry_count += 1
            if retry_count < max_retries:
                console.print(f"[yellow]连接失败，{retry_delay}秒后重试 ({retry_count}/{max_retries})...")
                await asyncio.sleep(retry_delay)
                # 增加重试延迟
                retry_delay *= 1.5
            else:
                console.print("[red]连接失败次数过多，放弃重试")
                return
            continue
        else:
            # 连接成功，重置重试计数
            retry_count = 0
            break
    
    console.print("[green]连接成功\n")
    
    # 导入内存监控模块
    try:
        from util.memory_monitor import cleanup_memory
    except ImportError:
        cleanup_memory = None
        
    try:
        message_count = 0
        while True:
            # 接收消息
            try:
                #message = await asyncio.wait_for(Cosmic.websocket.recv(), timeout=30)
                message = await asyncio.wait_for(Cosmic.websocket.recv(), None)
                message = json.loads(message)
                text = message["text"]
                delay = message["time_complete"] - message["time_submit"]
                print('message:',message)
                # 计数器增加
                message_count += 1
                
                # 每处理10条消息，执行一次内存清理
                if message_count % 10 == 0 and cleanup_memory:
                    await asyncio.to_thread(cleanup_memory)
                
                # 如果非最终结果，继续等待
                if not message["is_final"]:
                    print("not final text:",text)
                    continue
            except asyncio.TimeoutError:
                console.print("[yellow]等待消息超时，重新连接...")
                await Cosmic.websocket.close()
                await recv_result()
                return
            except json.JSONDecodeError:
                console.print("[red]无效的JSON格式")
                return
            # 消除末尾标点
            text = strip_punc(text)

            # 热词替换
            text = hot_sub(text)
            convert_to_traditional_chinese_done = False
            traditional_text = None
            if Config.convert_to_traditional_chinese_main == "繁":
                # 简繁转换
                converter = opencc.OpenCC(Config.opencc_converter)
                traditional_text = converter.convert(text)
                convert_to_traditional_chinese_done = True
                
            # 离线翻译
            offline_translate_done = False
            if Cosmic.offline_translate_needed and not Cosmic.transcribe_subtitles:
                offline_translated_text = await translate_offline(text)
                offline_translate_done = True
                Cosmic.offline_translate_needed = False

            # 在线翻译
            online_translate_done = False
            if Cosmic.online_translate_needed and not Cosmic.transcribe_subtitles:
                online_translated_text = translate_online(text)
                online_translate_done = True
                Cosmic.online_translate_needed = False

            if Config.save_audio:
                # 重命名录音文件
                file_audio = rename_audio(
                    message["task_id"], text, message["time_start"]
                )
            else:
                file_audio = None

            if Config.save_markdown:
                # 记录写入 md 文件
                if Config.convert_to_traditional_chinese_main == "繁" and traditional_text:
                    write_md(traditional_text, message["time_start"], file_audio)
                else:
                    write_md(text, message["time_start"], file_audio)

            # 控制台输出
            console.print(f"    转录时延：{delay:.2f}s")
            console.print(f"    识别结果：[green]{text}")


            if offline_translate_done:
                console.print(f"    离线翻译结果：[green]{offline_translated_text}")
            if online_translate_done:
                console.print(f"    在线翻译结果：[green]{online_translated_text}")
            if convert_to_traditional_chinese_done and Cosmic.opposite_state:
                console.print(f"    简繁转换结果：[green]{traditional_text}")
            console.line()
            # 打字
            if offline_translate_done:
                await type_result(offline_translated_text)
                offline_translate_done = False
            elif online_translate_done:
                await type_result(online_translated_text)
                online_translate_done = False
            elif convert_to_traditional_chinese_done and traditional_text:
                # 根据'简/繁'转换设定,来选择输出内容的逻辑
                if Config.convert_to_traditional_chinese_main == "繁":
                    if Cosmic.opposite_state:
                        await type_result(text)
                    else:
                        await type_result(traditional_text)
                else:
                    if Cosmic.opposite_state:
                        await type_result(traditional_text)
                    else:
                        await type_result(text)
            else:
                await type_result(text)
            convert_to_traditional_chinese_done = False
            Cosmic.opposite_state = False
            # result = await call_deepseek_api(text, action="polish")
            # asyncio.create_task(polish_text_async(text))
    except websockets.ConnectionClosedError:
        console.print("[red]连接断开\n")
    except websockets.ConnectionClosedOK:
        console.print("[red]连接断开\n")
    except KeyboardInterrupt:
        console.print("[yellow]接收到退出信号\n")
        if Cosmic.websocket:
            await Cosmic.websocket.close()
    except Exception as e:
        print(e)
    finally:
        return

async def polish_text_async(text):
    """异步处理文本润色，不阻塞主流程"""
    try:
        result = await call_deepseek_api(text, action="polish")
        result = await call_doubao_api(text, action="polish")

        console.print(f"    润色结果：[green]{result}")
    except Exception as e:
        console.print(f"    润色处理出错：[red]{str(e)}")

if __name__ == "__main__":
    None
