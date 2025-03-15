# DeepSeek API客户端

import json
import asyncio
import websockets

from util.config import ClientConfig
from util.config import DeepSeekConfig
from util.client_check_websocket import check_websocket
from util.client_cosmic import console


async def process_text_with_deepseek(text, action="polish"):
    """使用DeepSeek API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
    
    Returns:
        处理后的文本
    """
    try:
        # 连接到DeepSeek服务
        uri = f"ws://{ClientConfig.addr}:{DeepSeekConfig.deepseek_port}"
        async with websockets.connect(uri) as websocket:
            # 发送请求
            await websocket.send(json.dumps({
                "text": text,
                "action": action
            }))
            
            # 接收响应
            response = await websocket.recv()
            data = json.loads(response)
            
            if "error" in data:
                console.print(f"[red]处理文本时出错: {data['error']}")
                return None
            
            return data.get("processed_text")
    
    except Exception as e:
        console.print(f"[red]连接DeepSeek服务失败: {str(e)}")
        console.print("[yellow]请确保服务端已启动并启用了DeepSeek服务")
        return None


async def polish_text(text):
    """润色文本
    
    Args:
        text: 要润色的文本
    
    Returns:
        润色后的文本
    """
    return await process_text_with_deepseek(text, "polish")


async def summarize_text(text):
    """总结文本
    
    Args:
        text: 要总结的文本
    
    Returns:
        总结后的文本
    """
    return await process_text_with_deepseek(text, "summarize")


async def custom_process_text(text, action):
    """自定义处理文本
    
    Args:
        text: 要处理的文本
        action: 自定义操作描述
    
    Returns:
        处理后的文本
    """
    return await process_text_with_deepseek(text, action)


if __name__ == "__main__":
    # 测试代码
    async def test():
        text = "我今天很开心，因为我完成了一个项目。"
        print("原文:", text)
        
        # 测试润色
        polished = await polish_text(text)
        print("\n润色后:", polished)
        
        # 测试总结
        summary = await summarize_text(text)
        print("\n总结后:", summary)
        
        # 测试自定义处理
        custom = await custom_process_text(text, "改写成正式的工作汇报")
        print("\n改写后:", custom)
    
    asyncio.run(test())