# 启动DeepSeek API服务

# 测试
# websocat ws://localhost:6018/
# {"text": "请润色这段文字：我今天很开心，因为我完成了一个项目。", "action": "polish"}

import asyncio
import json
import httpx
from multiprocessing import Process

import websockets

from util.config import ClientConfig
from util.config import ServerConfig as Config
from util.config import DeepSeekConfig


# 定义DeepSeek API调用函数
async def call_deepseek_api(text, action="polish"):
    #如果text是空，直接返回
    if len(text) == 0:
      return
    
    
    """调用DeepSeek API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
    
    Returns:
        处理后的文本
    """
    try:
        headers = {
            "Authorization": f"Bearer {DeepSeekConfig.api_key}",
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
            "model": DeepSeekConfig.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": DeepSeekConfig.temperature,
            "max_tokens": DeepSeekConfig.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DeepSeekConfig.api_endpoint,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"处理文本时出错: {str(e)}"


# 定义WebSocket处理函数
async def deepseek_server(websocket, path):
    async for message in websocket:
        try:
            data = json.loads(message)
            text_to_process = data.get("text", "")
            action = data.get("action", "polish")
            
            # 调用DeepSeek API
            processed_text = await call_deepseek_api(text_to_process, action)
            
            # 将处理结果发送回客户端
            await websocket.send(json.dumps({"processed_text": processed_text}))
        
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"error": "无效的JSON格式"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))


def run_deepseek_service():
    """启动DeepSeek服务"""
    start_server = websockets.serve(
        deepseek_server, ClientConfig.addr, DeepSeekConfig.deepseek_port
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    # 启动DeepSeek WebSocket服务器
    server_process = Process(target=run_deepseek_service)
    server_process.start()



