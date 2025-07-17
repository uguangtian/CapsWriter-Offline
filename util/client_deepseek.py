# DeepSeek API客户端

import json
import asyncio
import websockets
from feishu import FeishuClient

from util.config import ClientConfig
from util.config import DeepSeekConfig
from util.client_check_websocket import check_websocket
from util.client_cosmic import console


async def process_text_with_deepseek(text, action="polish", feishu_doc_id=None):
    """使用DeepSeek API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
        feishu_doc_id: 飞书文档ID，如果提供则会将处理结果更新到对应文档
    
    Returns:
        处理后的文本，处理失败则返回None
    """
    # 检查输入文本是否为空
    if not text or len(text.strip()) == 0:
        console.print("[yellow]警告: 输入文本为空，无法处理")
        return None
        
    try:
        # 连接到DeepSeek服务
        uri = f"ws://{ClientConfig.addr}:{DeepSeekConfig.deepseek_port}"
        console.print(f"[blue]正在连接DeepSeek服务: {uri}")
        
        # 构建请求数据
        request_data = {
            "text": text,
            "action": action
        }
        
        # 如果提供了飞书文档ID，则添加到请求中
        if feishu_doc_id:
            request_data["feishu_doc_id"] = feishu_doc_id
            
        async with websockets.connect(uri, timeout=60) as websocket:
            # 发送请求
            await websocket.send(json.dumps(request_data))
            console.print(f"[blue]已发送{action}请求，文本长度: {len(text)}")
            
            # 接收响应
            response = await websocket.recv()
            data = json.loads(response)
            
            if "error" in data:
                console.print(f"[red]处理文本时出错: {data['error']}")
                return None
            
            processed_text = data.get("processed_text")
            console.print(f"[green]文本处理成功，结果长度: {len(processed_text) if processed_text else 0}")
            
            # 如果提供了飞书文档ID但服务端未处理，则在客户端处理
            if feishu_doc_id and not request_data.get("feishu_doc_id"):
                console.print(f"[blue]正在更新飞书文档: {feishu_doc_id}")
                feishu_client = FeishuClient()
                update_result = await feishu_client.update_document(feishu_doc_id, processed_text)
                if update_result:
                    console.print("[green]飞书文档更新成功")
                else:
                    console.print("[yellow]飞书文档更新失败")
                    
            return processed_text
    
    except asyncio.TimeoutError:
        console.print("[red]连接DeepSeek服务超时，请检查服务是否启动")
        return None
    except websockets.exceptions.ConnectionError:
        console.print("[red]无法连接到DeepSeek服务，请确保服务端已启动")
        return None
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