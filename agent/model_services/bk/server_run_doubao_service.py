# 启动豆包 API服务

# 测试
# websocat ws://localhost:6019/
# {"text": "请润色这段文字：我今天很开心，因为我完成了一个项目。", "action": "polish"}

import asyncio
import json
import httpx
from multiprocessing import Process

import websockets

from util.config import ClientConfig
from util.config import ServerConfig as Config
from util.config import DoubaoConfig


# 定义豆包 API调用函数
async def call_doubao_api(text, action="polish"):
    # 如果text是空，直接返回
    if len(text) == 0:
        return
    
    """调用豆包 API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
    
    Returns:
        处理后的文本
    """
    try:
        headers = {
            "Authorization": f"Bearer {DoubaoConfig.api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据不同的action构建不同的prompt
        if action == "polish":
            prompt = f"这个文本是使用语音输入的，可能有失误，词语不准确或者句意不通，请润色调整一下，尽量保持原句，只更可能错误的词语，补充标符号。简洁而不需要给出解释，只需要给出润色后的文本：\n\n{text}"
        elif action == "summarize":
            prompt = f"请总结以下文本的要点：\n\n{text}"
        else:
            prompt = f"请{action}以下文本：\n\n{text}"
        
        payload = {
            "model": DoubaoConfig.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": DoubaoConfig.temperature,
            "max_tokens": DoubaoConfig.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DoubaoConfig.api_endpoint,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                # 调整豆包API的返回结构解析
                return result["choices"][0]["message"]["content"]
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"处理文本时出错: {str(e)}"


# 定义WebSocket处理函数
async def doubao_server(websocket, path):
    print(f"[豆包] 新的WebSocket连接已建立")
    try:
        async for message in websocket:
            try:
                # 解析请求数据
                data = json.loads(message)
                text_to_process = data.get("text", "")
                action = data.get("action", "polish")
                save_to_file = data.get("save_to_file", False)
                output_filename = data.get("output_filename", None)
                
                print(f"[豆包] 收到请求: action={action}, text长度={len(text_to_process)}")
                
                # 使用文本润色服务处理文本
                from util.text_polish_service import TextPolishService
                polish_service = TextPolishService(model_type='doubao')
                
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
                    processed_text = await call_doubao_api(text_to_process, action)
                    # 将处理结果发送回客户端
                    await websocket.send(json.dumps({"processed_text": processed_text}))
                
                print(f"[豆包] 请求处理完成: action={action}")
            
            except json.JSONDecodeError:
                error_msg = "无效的JSON格式"
                print(f"[豆包] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
            except Exception as e:
                error_msg = str(e)
                print(f"[豆包] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
    except Exception as e:
        print(f"[豆包] WebSocket连接异常: {str(e)}")
    finally:
        print(f"[豆包] WebSocket连接已关闭")


def run_doubao_service():
    """启动豆包服务"""
    start_server = websockets.serve(
        doubao_server, ClientConfig.addr, DoubaoConfig.doubao_port
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    # 启动豆包 WebSocket服务器
    print(f"[豆包] 正在启动服务，监听地址: {ClientConfig.addr}:{DoubaoConfig.doubao_port}")
    server_process = Process(target=run_doubao_service)
    server_process.start()