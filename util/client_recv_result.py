import asyncio
import json

import keyboard
import websockets
from config import ClientConfig as Config
from util.client_cosmic import Cosmic, console
from util.client_check_websocket import check_websocket
from util.client_hot_sub import hot_sub
from util.client_rename_audio import rename_audio
from util.client_strip_punc import strip_punc
from util.client_write_md import write_md
from util.client_type_result import type_result

from transformers import pipeline, AutoModelWithLMHead, AutoTokenizer
import warnings
warnings.filterwarnings ('ignore')

#翻译
if Config.translate:
    modelName = ".\models\Helsinki-NLP--opus-mt-zh-en"
    console.print('正在加载翻译模型......')
    # 加载模型
    model = AutoModelWithLMHead.from_pretrained(modelName, local_files_only=True)
    # 加载分词器
    tokenizer = AutoTokenizer.from_pretrained(modelName, local_files_only=True)
    # 创建翻译管道
    translation = pipeline('translation_zh_to_en', model=model, tokenizer=tokenizer)
    console.print('翻译模型加载完成')


async def recv_result():
    if not await check_websocket():
        return
    console.print('[green]连接成功\n')
    try:
        while True:
            # 接收消息
            message = await Cosmic.websocket.recv()
            message = json.loads(message)
            text = message['text']
            delay = message['time_complete'] - message['time_submit']

            # 如果非最终结果，继续等待
            if not message['is_final']:
                continue

            # 消除末尾标点
            text = strip_punc(text)

            # 热词替换
            text = hot_sub(text)

            # 翻译
            if Config.translate:
                trans_text = translation(text)[0]['translation_text']

            if Config.save_audio:
                # 重命名录音文件
                file_audio = rename_audio(message['task_id'], text, message['time_start'])

                # 记录写入 md 文件
                write_md(text, message['time_start'], file_audio)

            # 控制台输出
            console.print(f'    转录时延：{delay:.2f}s')
            console.print(f'    识别结果：[green]{text}')
            if Config.translate:
                console.print(f'    翻译结果：[green]{trans_text}')
            console.line()

            # 打字
            if Config.translate:
                await type_result(trans_text)
            else:
                await type_result(text)


    except websockets.ConnectionClosedError:
        console.print('[red]连接断开\n')
    except websockets.ConnectionClosedOK:
        console.print('[red]连接断开\n')
    except Exception as e:
        print(e)
    finally:
        return
