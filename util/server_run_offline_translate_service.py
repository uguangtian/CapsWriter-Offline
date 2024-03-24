# 启动离线翻译服务

# 测试
# websocat ws://localhost:6017/
# {"text": "你好，世界！"}

# .\runtime\python.exe .\util\client_translate_online.py



import asyncio
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import websockets
from multiprocessing import Process
from config import ServerConfig as Config
from config import ClientConfig
from config import ModelPaths

#离线翻译
modelName = ModelPaths.opus_mt_dir
# 加载模型
model = AutoModelForSeq2SeqLM.from_pretrained(modelName, local_files_only=True)
# 加载分词器
tokenizer = AutoTokenizer.from_pretrained(modelName, local_files_only=True)

# 定义翻译函数
async def translate_text(text):
    # 分词
    input_ids = tokenizer.encode(text, return_tensors="pt")

    # 获取离线翻译结果
    outputs = model.generate(input_ids)
    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return translated_text

# 定义WebSocket处理函数
async def offline_translate_server(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        text_to_translate = data.get('text', '')

        # 调用翻译函数
        translated_text = await translate_text(text_to_translate)

        # 将离线翻译结果发送回客户端
        await websocket.send(json.dumps({'translated_text': translated_text}))

def run_offline_translate_service():
    start_server = websockets.serve(offline_translate_server, ClientConfig.addr, Config.offline_translate_port)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    # 启动离线翻译 WebSocket服务器
    server_process = Process(target=run_offline_translate_service)
    server_process.start()
