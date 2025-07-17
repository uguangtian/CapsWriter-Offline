# DeepSeek API服务

import asyncio
import json
import httpx
from typing import Dict, Any, Optional

# 导入配置
from util.config import DeepSeekConfig
# from global_config import DeepSeekConfig  # 导入全局配置模块


async def call_deepseek_api(text: str, action: str = "polish", **kwargs) -> str:
    """调用DeepSeek API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
        **kwargs: 额外参数，如feishu_doc_id等
    
    Returns:
        处理后的文本，如果处理失败则返回错误信息
    """
    # 如果text是空，直接返回
    if not text or len(text.strip()) == 0:
        return "输入文本为空，无法处理"
    
    # 获取额外参数
    feishu_doc_id = kwargs.get('feishu_doc_id', None)
    temperature = kwargs.get('temperature', DeepSeekConfig.temperature)
    max_tokens = kwargs.get('max_tokens', DeepSeekConfig.max_tokens)
    model = kwargs.get('model', DeepSeekConfig.model)
    api_key = kwargs.get('api_key', DeepSeekConfig.api_key)
    api_endpoint = kwargs.get('api_endpoint', DeepSeekConfig.api_endpoint)
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 根据不同的action构建不同的prompt
        if action == "polish":
            prompt = f"这个文本是使用语音输入的，可能有失误，词语不准确或者句意不通，请润色调整一下，尽量保持原句，只更可能错误的词语，补充标符号。简洁而不需要给出解释，只需要给出润色后的文本：\n\n{text}"
        elif action == "summarize":
            prompt = f"请总结以下文本的要点：\n\n{text}"
        elif action == "translate":
            prompt = f"将以下文本翻译成中文，要求信达雅：\n\n{text}"
        elif action == "code_optimizer":
            prompt = f"请优化下列代码，不要改变函数签名，尽量增加中文注释，只返回代码，不用解释\n\n{text}"
        else:
            prompt = f"请{action}以下文本：\n\n{text}"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                api_endpoint,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                processed_text = result["choices"][0]["message"]["content"]
                
                # 如果提供了飞书文档ID，则更新文档
                if feishu_doc_id:
                    from feishu import FeishuClient
                    feishu_client = FeishuClient()
                    await feishu_client.update_document(feishu_doc_id, processed_text)
                    
                return processed_text
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"处理文本时出错: {str(e)}"


# WebSocket服务器实现
async def deepseek_server(websocket):
    """处理WebSocket连接和请求
    
    Args:
        websocket: WebSocket连接对象
        path: 请求路径
    """
    print(f"[DeepSeek] 新的WebSocket连接已建立")
    try:
        async for message in websocket:
            try:
                # 解析请求数据
                data = json.loads(message)
                text_to_process = data.get("text", "")
                action = data.get("action", "polish")
                feishu_doc_id = data.get("feishu_doc_id", None)
                save_to_file = data.get("save_to_file", False)
                output_filename = data.get("output_filename", None)
                
                print(f"[DeepSeek] 收到请求: action={action}, text长度={len(text_to_process)}")
                
                # 使用文本润色服务处理文本
                if save_to_file:
                    # 处理文本并保存到文件
                    from text_polish_service import TextPolishService
                    polish_service = TextPolishService(model_type='deepseek')
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
                    processed_text = await call_deepseek_api(
                        text_to_process, 
                        action, 
                        feishu_doc_id=feishu_doc_id
                    )
                    # 将处理结果发送回客户端
                    await websocket.send(json.dumps({"processed_text": processed_text}))
                
                print(f"[DeepSeek] 请求处理完成: action={action}")
            
            except json.JSONDecodeError:
                error_msg = "无效的JSON格式"
                print(f"[DeepSeek] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
            except Exception as e:
                error_msg = str(e)
                print(f"[DeepSeek] 错误: {error_msg}")
                await websocket.send(json.dumps({"error": error_msg}))
    except Exception as e:
        print(f"[DeepSeek] WebSocket连接异常: {str(e)}")
    finally:
        print(f"[DeepSeek] WebSocket连接已关闭")


def run_deepseek_service(host="127.0.0.1", port=None):
    """启动DeepSeek服务
    
    Args:
        host: 服务主机地址
        port: 服务端口，如果为None则使用配置中的端口
    """
    import websockets
    from util.config import ClientConfig
    
    if port is None:
        port = DeepSeekConfig.deepseek_port
    
    start_server = websockets.serve(
        deepseek_server, host, port
    )
    print(f"[DeepSeek] 正在启动服务，监听地址: {host}:{port}")
    
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()