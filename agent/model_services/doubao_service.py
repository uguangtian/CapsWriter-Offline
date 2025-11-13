# 豆包 API服务

import asyncio
import json
import httpx
import time
from typing import Dict, Any, Optional

# 导入配置
from util.config import DoubaoConfig
# 导入日志工具
from .logger_utils import doubao_logger


async def call_doubao_api(text: str, action: str = "polish", **kwargs) -> str:
    """调用豆包 API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
        **kwargs: 额外参数
    
    Returns:
        处理后的文本，如果处理失败则返回错误信息
    """
    # 如果text是空，直接返回
    if not text or len(text.strip()) == 0:
        return "输入文本为空，无法处理"
    
    # 获取额外参数
    temperature = kwargs.get('temperature', DoubaoConfig.temperature)
    max_tokens = kwargs.get('max_tokens', DoubaoConfig.max_tokens)
    model = kwargs.get('model', DoubaoConfig.model)
    api_key = kwargs.get('api_key', DoubaoConfig.api_key)
    api_endpoint = kwargs.get('api_endpoint', DoubaoConfig.api_endpoint)
    
    # 记录请求开始时间
    start_time = time.time()
    
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
        
        # 记录API请求日志
        request_params = {
            "api_endpoint": api_endpoint,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "api_key": api_key,
            "headers": headers,
            "payload": payload
        }
        request_id = doubao_logger.log_api_request(action, len(text), request_params)
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                api_endpoint,
                json=payload,
                headers=headers
            )
            
            # 计算请求耗时
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                processed_text = result["choices"][0]["message"]["content"]
                
                # 记录成功响应日志
                doubao_logger.log_api_response(
                    request_id=request_id,
                    success=True,
                    response_data=result,
                    response_length=len(processed_text),
                    duration_ms=duration_ms
                )
                
                return processed_text
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                # 记录失败响应日志
                doubao_logger.log_api_response(
                    request_id=request_id,
                    success=False,
                    error_message=error_msg,
                    duration_ms=duration_ms
                )
                return error_msg
    
    except Exception as e:
        # 计算请求耗时
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"处理文本时出错: {str(e)}"
        
        # 记录异常日志
        try:
            doubao_logger.log_api_response(
                request_id=request_id if 'request_id' in locals() else "unknown",
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )
        except:
            doubao_logger.error(f"记录异常日志失败: {error_msg}")
        
        return error_msg


# WebSocket服务器实现
async def doubao_server(websocket):
    """处理WebSocket连接和请求
    
    Args:
        websocket: WebSocket连接对象
        path: 请求路径
    """
    doubao_logger.log_websocket_event("connection_established")
    try:
        async for message in websocket:
            try:
                # 解析请求数据
                data = json.loads(message)
                text_to_process = data.get("text", "")
                action = data.get("action", "polish")
                save_to_file = data.get("save_to_file", False)
                output_filename = data.get("output_filename", None)
                
                # 记录WebSocket消息接收日志
                doubao_logger.log_websocket_event("message_received", {
                    "action": action,
                    "text_length": len(text_to_process),
                    "save_to_file": save_to_file
                })
                
                # 使用文本润色服务处理文本
                if save_to_file:
                    # 处理文本并保存到文件
                    from text_polish_service import TextPolishService
                    polish_service = TextPolishService(model_type='doubao')
                    processed_text, file_path = await polish_service.polish_text(
                        text_to_process, action, output_filename
                    )
                    # 将处理结果和文件路径发送回客户端
                    response_data = {
                        "processed_text": processed_text,
                        "file_path": file_path
                    }
                    await websocket.send(json.dumps(response_data))
                    doubao_logger.info(f"文件保存完成: {file_path}")
                else:
                    # 只处理文本，不保存到文件
                    processed_text = await call_doubao_api(text_to_process, action)
                    # 将处理结果发送回客户端
                    response_data = {"processed_text": processed_text}
                    await websocket.send(json.dumps(response_data))
                
                doubao_logger.info(f"WebSocket请求处理完成: action={action}, 响应长度={len(processed_text)}")
            
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


def run_doubao_service(host="127.0.0.1", port=None):
    """启动豆包服务
    
    Args:
        host: 服务主机地址
        port: 服务端口，如果为None则使用配置中的端口
    """
    import websockets
    from util.config import ClientConfig
    
    if port is None:
        port = DoubaoConfig.doubao_port if hasattr(DoubaoConfig, 'doubao_port') else 6019
    
    start_server = websockets.serve(
        doubao_server, host, port
    )
    print(f"[豆包] 正在启动服务，监听地址: {host}:{port}")
    
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()