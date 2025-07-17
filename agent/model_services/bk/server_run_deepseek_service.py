# 启动DeepSeek API服务

# 测试
# websocat ws://localhost:6018/
# {"text": "请润色这段文字：我今天很开心，因为我完成了一个项目。", "action": "polish"}

import asyncio
import json
import httpx
from multiprocessing import Process

import websockets
from feishu import FeishuClient

from util.config import ClientConfig
from util.config import ServerConfig as Config
from util.config import DeepSeekConfig


# 定义DeepSeek API调用函数
async def call_deepseek_api(text, action="polish", feishu_doc_id=None):
    """调用DeepSeek API处理文本
    
    Args:
        text: 要处理的文本
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
        feishu_doc_id: 飞书文档ID，如果提供则会将处理结果更新到对应文档
    
    Returns:
        处理后的文本，如果处理失败则返回错误信息
    """
    # 如果text是空，直接返回
    if not text or len(text.strip()) == 0:
        return "输入文本为空，无法处理"
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
                processed_text = result["choices"][0]["message"]["content"]
                
                # 如果提供了飞书文档ID，则更新文档
                if feishu_doc_id:
                    feishu_client = FeishuClient()
                    await feishu_client.update_document(feishu_doc_id, processed_text)
                    
                return processed_text
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"处理文本时出错: {str(e)}"


# 定义WebSocket处理函数
async def deepseek_server(websocket, path):
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
                
                if save_to_file or len(text_to_process) > 1000:
                    # 使用文本润色服务处理长文本或需要保存到文件的请求
                    from util.text_polish_service import TextPolishService
                    polish_service = TextPolishService(model_type='deepseek')
                    
                    # 处理文本并保存到文件（如果需要）
                    processed_text, file_path = await polish_service.polish_text(
                        text_to_process, action, output_filename if save_to_file else None
                    )
                    
                    # 如果提供了飞书文档ID，则更新文档
                    if feishu_doc_id:
                        feishu_client = FeishuClient()
                        await feishu_client.update_document(feishu_doc_id, processed_text)
                    
                    # 将处理结果和文件路径（如果有）发送回客户端
                    response_data = {"processed_text": processed_text}
                    if save_to_file:
                        response_data["file_path"] = file_path
                    
                    await websocket.send(json.dumps(response_data))
                else:
                    # 对于短文本，直接调用API处理
                    processed_text = await call_deepseek_api(text_to_process, action, feishu_doc_id)
                    
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


def run_deepseek_service():
    """启动DeepSeek服务"""
    print(f"[DeepSeek] 正在启动服务，监听地址: {ClientConfig.addr}:{DeepSeekConfig.deepseek_port}")
    start_server = websockets.serve(
        deepseek_server, ClientConfig.addr, DeepSeekConfig.deepseek_port
    )
    asyncio.get_event_loop().run_until_complete(start_server)
    print(f"[DeepSeek] 服务已启动，等待连接...")
    asyncio.get_event_loop().run_forever()


async def test_deepseek_service():
    """测试DeepSeek服务是否可用"""
    try:
        # 测试连接
        test_text = "测试连接"
        result = await call_deepseek_api(test_text, action="polish")
        print(f"[DeepSeek] 服务测试结果: {result}")
        return True
    except Exception as e:
        print(f"[DeepSeek] 服务测试失败: {e}")
        return False


if __name__ == "__main__":
    # 启动DeepSeek WebSocket服务器
    server_process = Process(target=run_deepseek_service)
    server_process.start()
    
    # 等待服务启动
    time.sleep(2)
    
    # 测试服务
    asyncio.run(test_deepseek_service())



