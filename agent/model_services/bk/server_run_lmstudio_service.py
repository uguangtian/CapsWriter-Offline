# 启动LM Studio本地模型服务

import asyncio
import json
from multiprocessing import Process

import httpx
import websockets

from util.config import ClientConfig
from util.config import ServerConfig as Config
from util.config import LMStudioConfig


# 定义LM Studio API调用函数
async def call_lmstudio_api(text: str, action: str = "polish", stream: bool = False, stream_callback = None) -> str:
    """调用LM Studio API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'translate'(翻译)等
        stream: 是否使用流式响应
        stream_callback: 流式响应的回调函数
    
    Returns:
        str: 处理后的文本或错误信息
    """
    # 如果text是空，直接返回
    if not text or len(text.strip()) == 0:
        return "输入文本为空，无法处理"
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        # 根据不同的action构建不同的prompt
        if action == "polish":
            prompt = f"这个文本是使用语音输入的，可能有失误，词语不准确或者句意不通，请润色调整一下，尽量保持原句，只更可能错误的词语，补充标符号。简洁而不需要给出解释，只需要给出润色后的文本：\n\n{text}"
        elif action == "translate":
            prompt = f"将以下文本翻译成中文，要求信达雅，只给出翻译后的文本，其他的都不要\n\n{text}"
        else:
            prompt = f"请{action}以下文本：\n\n{text}"
        
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": LMStudioConfig.temperature,
            "max_tokens": LMStudioConfig.max_tokens,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(LMStudioConfig.api_endpoint, json=payload, headers=headers)
            
            if response.status_code != 200:
                return f"API调用失败: {response.status_code} - {response.text}"
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "响应数据格式错误"

    
    except Exception as e:
        return f"处理文本时出错: {str(e)}"


# 定义WebSocket处理函数
async def lmstudio_server(websocket, path):
    print(f"[LM Studio] 新的WebSocket连接已建立")
    try:
        async for message in websocket:
            try:
                # 解析请求数据
                data = json.loads(message)
                text_to_process = data.get("text", "")
                action = data.get("action", "polish")
                save_to_file = data.get("save_to_file", False)
                output_filename = data.get("output_filename", None)
                
                print(f"[LM Studio] 收到请求: action={action}, text长度={len(text_to_process)}")
                
                # 使用文本润色服务处理文本
                from util.text_polish_service import TextPolishService
                polish_service = TextPolishService(model_type='lmstudio')
                
                if save_to_file:
                    # 处理文本并保存到文件
                    processed_text, file_path = await polish_service.polish_text(
                        text_to_process, action, output_filename
                    )
                    # 将处理结果和文件路径发送回客户端
                    await websocket.send(json.dumps({
                        "processed_text": processed_text,
                        "file_path": file_path
                    }))
                else:
                    # 只处理文本，不保存到文件
                    processed_text = await call_lmstudio_api(text_to_process, action)
                    # 将处理结果发送回客户端
                    await websocket.send(json.dumps({"processed_text": processed_text}))
                
                print(f"[LM Studio] 请求处理完成: action={action}")
            
            except json.JSONDecodeError:
                error_msg = "无效的JSON格式"
                print(f"[LM Studio] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
            except Exception as e:
                error_msg = str(e)
                print(f"[LM Studio] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
    except Exception as e:
        print(f"[LM Studio] WebSocket连接异常: {str(e)}")
    finally:
        print(f"[LM Studio] WebSocket连接已关闭")


def run_lmstudio_service():
    """启动LM Studio服务"""
    start_server = websockets.serve(
        lmstudio_server, ClientConfig.addr, LMStudioConfig.lmstudio_port
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    # 启动LM Studio WebSocket服务器
    print(f"[LM Studio] 正在启动服务，监听地址: {ClientConfig.addr}:{LMStudioConfig.lmstudio_port}")
    server_process = Process(target=run_lmstudio_service)
    server_process.start()