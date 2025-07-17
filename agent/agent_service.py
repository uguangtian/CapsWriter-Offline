# 智能体代理服务

import asyncio
import json
import websockets
from typing import Dict, Any, Optional, List, Union
from multiprocessing import Process

from agent.base_agent import BaseAgent
from agent.text_polish_agent import TextPolishAgent
from util.config import DeepSeekConfig, DoubaoConfig, LMStudioConfig, ClaudeConfig
from typing import Dict, Any, Optional, Tuple, Union


class AgentService:
    """智能体代理服务
    
    管理和协调不同类型的智能体，提供统一的WebSocket接口供外部调用。
    支持动态创建和配置不同类型的智能体。
    
    Attributes:
        agents: 注册的智能体字典，键为智能体名称，值为智能体实例
        host: 服务主机地址
        port: 服务端口
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 6020):
        """初始化智能体代理服务
        
        Args:
            host: 服务主机地址
            port: 服务端口
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.host = host
        self.port = port
        
        # 注册默认智能体
        self._register_default_agents()
    
    def _register_default_agents(self):
        """注册默认智能体"""
        # 注册文本润色智能体
        self.register_agent(
            TextPolishAgent(model_type="deepseek"),
            "text_polish_deepseek"
        )
        self.register_agent(
            TextPolishAgent(model_type="doubao"),
            "text_polish_doubao"
        )
        self.register_agent(
            TextPolishAgent(model_type="lmstudio"),
            "text_polish_lmstudio"
        )
        self.register_agent(
            TextPolishAgent(model_type="claude"),
            "text_polish_claude"
        )
    
    def register_agent(self, agent: BaseAgent, name: Optional[str] = None):
        """注册智能体
        
        Args:
            agent: 要注册的智能体实例
            name: 智能体名称，如果为None则使用agent.name
        """
        agent_name = name or agent.name
        self.agents[agent_name] = agent
        print(f"已注册智能体: {agent_name}")
    
    def unregister_agent(self, name: str):
        """注销智能体
        
        Args:
            name: 要注销的智能体名称
        """
        if name in self.agents:
            del self.agents[name]
            print(f"已注销智能体: {name}")
    
    async def handle_request(self, websocket):
        """处理WebSocket请求
        
        Args:
            websocket: WebSocket连接对象
            path: 请求路径
        """
        print(f"[AgentService] 新的WebSocket连接已建立")
        try:
            async for message in websocket:
                try:
                    # 解析请求数据
                    data = json.loads(message)
                    agent_name = data.get("agent", "text_polish_deepseek")
                    action = data.get("action", "polish")
                    text = data.get("text", "")
                    save_to_file = data.get("save_to_file", False)
                    output_filename = data.get("output_filename", None)
                    
                    # 额外参数
                    kwargs = {
                        "save_to_file": save_to_file,
                        "output_filename": output_filename
                    }
                    
                    # 如果是DeepSeek，可能有飞书文档ID
                    if "deepseek" in agent_name:
                        kwargs["feishu_doc_id"] = data.get("feishu_doc_id", None)
                    
                    print(f"[AgentService] 收到请求: agent={agent_name}, action={action}, text长度={len(text)}")
                    
                    # 检查智能体是否存在
                    if agent_name not in self.agents:
                        await websocket.send(json.dumps({
                            "error": f"智能体 {agent_name} 不存在"
                        }))
                        continue
                    
                    # 调用智能体处理文本
                    agent = self.agents[agent_name]
                    result = await agent.process(text, action, **kwargs)
                    
                    # 根据返回类型构建响应
                    if isinstance(result, tuple) and len(result) == 2:
                        # 返回处理后的文本和文件路径
                        processed_text, file_path = result
                        await websocket.send(json.dumps({
                            "processed_text": processed_text,
                            "file_path": file_path
                        }))
                    else:
                        # 只返回处理后的文本
                        await websocket.send(json.dumps({
                            "processed_text": result
                        }))
                    
                    print(f"[AgentService] 请求处理完成: agent={agent_name}, action={action}")
                
                except json.JSONDecodeError:
                    error_msg = "无效的JSON格式"
                    print(f"[AgentService] 错误: {error_msg}")
                    await websocket.send(json.dumps({"error": error_msg}))
                except Exception as e:
                    error_msg = str(e)
                    print(f"[AgentService] 错误: {error_msg}")
                    await websocket.send(json.dumps({"error": error_msg}))
        except Exception as e:
            print(f"[AgentService] WebSocket连接异常: {str(e)}")
        finally:
            print(f"[AgentService] WebSocket连接已关闭")
    
    def start(self):
        """启动智能体代理服务"""
        # 创建WebSocket服务器
        start_server = websockets.serve(
            self.handle_request, self.host, self.port
        )
        print(f"[AgentService] 正在启动服务，监听地址: {self.host}:{self.port}")
        
        # 启动事件循环
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    
    def start_in_process(self):
        """在新进程中启动智能体代理服务"""
        process = Process(target=self._start_service)
        process.start()
        return process
    
    def _start_service(self):
        """启动服务的辅助方法，用于在新进程中调用"""
        asyncio.run(self._async_start_service())
    
    async def _async_start_service(self):
        """异步启动服务"""
        server = await websockets.serve(
            self.handle_request, self.host, self.port
        )
        print(f"[AgentService] 服务已启动，监听地址: {self.host}:{self.port}")
        await asyncio.Future()  # 保持服务运行


async def call_agent_service(text: str, 
                           agent: str = "text_polish_deepseek", 
                           action: str = "polish",
                           save_to_file: bool = False,
                           output_filename: Optional[str] = None,
                           host: str = "127.0.0.1",
                           port: int = 6020,
                           feishu_doc_id: Optional[str] = None) -> str:
    """调用智能体代理服务
    
    Args:
        text: 要处理的文本
        agent: 智能体名称，默认为"text_polish_deepseek"
        action: 操作类型，如'polish'(润色)、'summarize'(总结)等
        save_to_file: 是否保存到文件
        output_filename: 输出文件名，如果为None则自动生成
        host: 服务主机地址
        port: 服务端口
        feishu_doc_id: 飞书文档ID，仅在使用DeepSeek智能体时有效
        
    Returns:
        处理后的文本，如果save_to_file为True，则返回(处理后的文本, 文件路径)
    """
    # 构建请求数据
    request_data = {
        "agent": agent,
        "action": action,
        "text": text,
        "save_to_file": save_to_file,
        "output_filename": output_filename
    }
    
    # 如果是DeepSeek智能体，可能需要飞书文档ID
    if "deepseek" in agent and feishu_doc_id:
        request_data["feishu_doc_id"] = feishu_doc_id
    
    # 连接WebSocket服务器
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # 发送请求
            await websocket.send(json.dumps(request_data))
            print(f"已发送请求: agent={agent}, action={action}, text长度={len(text)}")
            
            # 接收响应
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # 检查是否有错误
            if "error" in response_data:
                print(f"错误: {response_data['error']}")
                return response_data['error']
            
            # 返回处理结果
            if save_to_file and "file_path" in response_data:
                # return response_data["processed_text"], response_data["file_path"]
                return response_data["processed_text"]

            else:
                return response_data["processed_text"]
    
    except Exception as e:
        print(f"连接服务器失败: {str(e)}")
        return f"连接服务器失败: {str(e)}"

