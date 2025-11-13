# DeepSeek API服务

import asyncio
import json
import httpx
import time
from typing import Dict, Any, Optional

# 导入配置
from util.config import DeepSeekConfig
# 导入日志工具
from .logger_utils import deepseek_logger
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
    
    # 记录请求开始时间
    start_time = time.time()
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 获取系统设定和用户设定
        system_prompt = kwargs.get('system_prompt', None)
        user_prompt = kwargs.get('user_prompt', None)
        
        # 构建默认的系统提示词
        default_system_prompts = {
            "polish": "你是一个专业的文本润色助手。你的任务是修正语音输入中的错误，包括错别字、语法错误和标点符号问题，同时保持原文的意思和风格。",
            "summarize": "你是一个专业的文本总结助手。你的任务是提取文本的关键信息，生成简洁明了的摘要。",
            "correct": "你是一个专业的文本纠错助手。你的任务是检测并修正文本中的拼写、语法和逻辑错误。",
            "extract_keywords": "你是一个专业的关键词提取助手。你的任务是从文本中提取最重要的关键词和短语。",
            "structure": "你是一个专业的文本结构化助手。你的任务是将文本按照逻辑关系进行整理和结构化。",
            "translate": "你是一个专业的翻译助手。你的任务是准确、流畅地翻译文本，保持原文的意思和风格。"
        }
        
        # 构建默认的用户提示词
        default_user_prompts = {
            "polish": "请润色以下文本，修正语音输入中的错误，补充标点符号，保持原意不变：",
            "summarize": "请总结以下文本的要点：",
            "correct": "请纠正以下文本中的错误：",
            "extract_keywords": "请从以下文本中提取关键词：",
            "structure": "请将以下文本进行结构化整理：",
            "translate": "请将以下文本翻译成中文："
        }
        
        # 使用自定义提示词或默认提示词
        final_system_prompt = system_prompt or default_system_prompts.get(action, "你是一个专业的文本处理助手。")
        final_user_prompt = user_prompt or default_user_prompts.get(action, f"请{action}以下文本：")
        
        # 构建完整的用户消息
        user_message = f"{final_user_prompt}\n\n{text}"
        
        # 构建消息列表
        messages = []
        if final_system_prompt:
            messages.append({"role": "system", "content": final_system_prompt})
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": model,
            "messages": messages,
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
        request_id = deepseek_logger.log_api_request(action, len(text), request_params)
        
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
                deepseek_logger.log_api_response(
                    request_id=request_id,
                    success=True,
                    response_data=result,
                    response_length=len(processed_text),
                    duration_ms=duration_ms
                )
                
                # 如果提供了飞书文档ID，则更新文档
                if feishu_doc_id:
                    from feishu import FeishuClient
                    feishu_client = FeishuClient()
                    await feishu_client.update_document(feishu_doc_id, processed_text)
                    deepseek_logger.info(f"已更新飞书文档: {feishu_doc_id}")
                    
                return processed_text
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                # 记录失败响应日志
                deepseek_logger.log_api_response(
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
            deepseek_logger.log_api_response(
                request_id=request_id if 'request_id' in locals() else "unknown",
                success=False,
                error_message=error_msg,
                duration_ms=duration_ms
            )
        except:
            deepseek_logger.error(f"记录异常日志失败: {error_msg}")
        
        return error_msg


# WebSocket服务器实现
async def deepseek_server(websocket):
    """处理WebSocket连接和请求
    
    Args:
        websocket: WebSocket连接对象
        path: 请求路径
    """
    deepseek_logger.log_websocket_event("connection_established")
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
                
                # 记录WebSocket消息接收日志
                deepseek_logger.log_websocket_event("message_received", {
                    "action": action,
                    "text_length": len(text_to_process),
                    "save_to_file": save_to_file,
                    "has_feishu_doc_id": feishu_doc_id is not None
                })
                
                # 使用文本润色服务处理文本
                if save_to_file:
                    # 处理文本并保存到文件
                    from text_polish_service import TextPolishService
                    polish_service = TextPolishService(model_type='deepseek')
                    processed_text, file_path = await polish_service.polish_text(
                        text_to_process, action, output_filename
                    )
                    # 将处理结果和文件路径发送回客户端
                    response_data = {
                        "processed_text": processed_text,
                        "file_path": file_path
                    }
                    await websocket.send(json.dumps(response_data))
                    deepseek_logger.info(f"文件保存完成: {file_path}")
                else:
                    # 只处理文本，不保存到文件
                    processed_text = await call_deepseek_api(
                        text_to_process, 
                        action, 
                        feishu_doc_id=feishu_doc_id
                    )
                    # 将处理结果发送回客户端
                    response_data = {"processed_text": processed_text}
                    await websocket.send(json.dumps(response_data))
                
                deepseek_logger.info(f"WebSocket请求处理完成: action={action}, 响应长度={len(processed_text)}")
            
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