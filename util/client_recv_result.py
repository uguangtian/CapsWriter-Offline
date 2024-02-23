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
from rich.markdown import Markdown
from transformers import pipeline, AutoModelWithLMHead, AutoTokenizer
import warnings
warnings.filterwarnings ('ignore')

#翻译
modelName = ".\models\Helsinki-NLP--opus-mt-zh-en"
console.rule('[bold #d55252]加载翻译模型')
# 加载模型
model = AutoModelWithLMHead.from_pretrained(modelName, local_files_only=True)
# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(modelName, local_files_only=True)
# 创建翻译管道
translation = pipeline('translation_zh_to_en', model=model, tokenizer=tokenizer)
markdown = (f'''

离线翻译模型 [Helsinki-NLP/opus-mt-zh-en](https://huggingface.co/Helsinki-NLP/opus-mt-zh-en) 加载完成

使用步骤：

1. 按住 `{Config.trans_shortcut}` 再按 `{Config.shortcut}` 进行翻译

注意事项：

1. 注意输入结束时，先松开 `{Config.shortcut}` 键，待输入完成，再松开 `{Config.trans_shortcut}` 键

''')
console.print(Markdown(markdown), highlight=True)


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
            translate = False
            if keyboard.is_pressed(Config.trans_shortcut):
                translate = True
            if translate:
                trans_text = translation(text)[0]['translation_text']

            if Config.save_audio:
                # 重命名录音文件
                file_audio = rename_audio(message['task_id'], text, message['time_start'])

                # 记录写入 md 文件
                write_md(text, message['time_start'], file_audio)

            # 控制台输出
            console.print(f'    转录时延：{delay:.2f}s')
            console.print(f'    识别结果：[green]{text}')
            if translate:
                console.print(f'    翻译结果：[green]{trans_text}')
            console.line()

            # 打字
            if translate:
                await type_result(trans_text)
                translate = False
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
