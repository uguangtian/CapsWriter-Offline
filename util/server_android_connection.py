import socket
import threading
import json
import time
import base64
import asyncio
import websockets
import atexit
from typing import Dict, List, Tuple, Optional

from util.server_cosmic import Cosmic, console
from util.server_classes import Task
from util.config import ServerConfig as Config

# 用于UDP广播发现的端口
DISCOVERY_PORT = 8888
# 使用与主WebSocket相同的端口，因为现在我们也使用WebSocket协议
WS_PORT = int(Config.speech_recognition_port)

# 存储Android客户端连接信息
class AndroidClients:
    clients: Dict[str, Tuple[websockets.WebSocketServerProtocol, str]] = {}
    clients_lock = threading.Lock()
    # 添加UDP套接字引用，方便后续清理
    udp_socket = None

    @classmethod
    def add_client(cls, client_id: str, websocket: websockets.WebSocketServerProtocol, client_addr: str):
        with cls.clients_lock:
            cls.clients[client_id] = (websocket, client_addr)
            console.print(f"[DEBUG] Android客户端已连接: {client_addr} (ID: {client_id})", style="green")
            console.print(f"[DEBUG] 当前连接的Android客户端数量: {len(cls.clients)}", style="cyan")

    @classmethod
    def remove_client(cls, client_id: str):
        with cls.clients_lock:
            if client_id in cls.clients:
                client_addr = cls.clients[client_id][1]
                del cls.clients[client_id]
                console.print(f"[DEBUG] Android客户端已断开: {client_addr} (ID: {client_id})", style="yellow")
                console.print(f"[DEBUG] 当前连接的Android客户端数量: {len(cls.clients)}", style="cyan")

    @classmethod
    def get_client(cls, client_id: str) -> Optional[Tuple[websockets.WebSocketServerProtocol, str]]:
        with cls.clients_lock:
            client = cls.clients.get(client_id)
            if client:
                console.print(f"[DEBUG] 获取到Android客户端: {client_id}", style="cyan")
            else:
                console.print(f"[DEBUG] 未找到Android客户端: {client_id}", style="yellow")
            return client
            
    @classmethod
    def cleanup(cls):
        """清理所有资源"""
        # 关闭UDP套接字
        if cls.udp_socket:
            try:
                cls.udp_socket.close()
                console.print("[DEBUG] 已关闭UDP广播套接字", style="cyan")
            except Exception as e:
                console.print(f"[DEBUG] 关闭UDP套接字时出错: {e}", style="red")
        
        # 关闭所有客户端连接
        with cls.clients_lock:
            console.print(f"[DEBUG] 开始清理 {len(cls.clients)} 个Android客户端连接", style="cyan")
            for client_id, (websocket, addr) in list(cls.clients.items()):
                try:
                    # 对于WebSocket，我们不能直接在这里关闭，因为它是异步的
                    # 但我们可以标记它们为已移除
                    console.print(f"[DEBUG] 标记客户端连接为已移除: {addr} (ID: {client_id})", style="yellow")
                except Exception as e:
                    console.print(f"[DEBUG] 标记客户端连接时出错: {e}", style="red")
            cls.clients.clear()
            console.print("[DEBUG] 所有Android客户端连接已清理完毕", style="green")

# 处理UDP广播发现请求
def handle_discovery_requests():
    """监听UDP广播请求并回复服务器信息"""
    # 确保每次创建新的套接字，避免重用已关闭的套接字
    try:
        console.print("[DEBUG] 正在初始化UDP广播监听...", style="cyan")
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # 保存UDP套接字引用，方便后续清理
        AndroidClients.udp_socket = udp_socket
        
        # 绑定到广播发现端口
        udp_socket.bind((Config.addr, DISCOVERY_PORT))
        
        console.print(f"[DEBUG] UDP广播监听已启动在 {Config.addr}:{DISCOVERY_PORT}", style="cyan")
        
        while True:
            try:
                console.print("[DEBUG] 等待UDP广播请求...", style="cyan")
                data, addr = udp_socket.recvfrom(1024)
                request = data.decode('utf-8')
                console.print(f"[DEBUG] 收到来自 {addr} 的UDP数据: {request}", style="cyan")
                
                # 检查是否是发现请求
                if request == "DISCOVER_CAPSWRITER_SERVER":
                    # 回复服务器信息，格式为 "IP:PORT"，使用WebSocket端口
                    local_ip = socket.gethostbyname(socket.gethostname())
                    response = f"{local_ip}:{WS_PORT}"
                    console.print(f"[DEBUG] 本机IP地址: {local_ip}", style="cyan")
                    udp_socket.sendto(response.encode('utf-8'), addr)
                    console.print(f"[DEBUG] 已回复发现请求: {response} 到 {addr}", style="green")
            except Exception as e:
                if isinstance(e, OSError) and e.errno == 9:  # Bad file descriptor
                    console.print("[DEBUG] UDP套接字已关闭，停止监听", style="yellow")
                    break
                console.print(f"[DEBUG] 处理UDP广播请求时出错: {e}", style="red")
    except KeyboardInterrupt:
        console.print("[DEBUG] UDP广播监听被中断", style="yellow")
    except Exception as e:
        console.print(f"[DEBUG] UDP广播监听初始化出错: {e}", style="red")
    finally:
        # 确保套接字被关闭
        if 'udp_socket' in locals() and udp_socket:
            try:
                udp_socket.close()
                console.print("[DEBUG] UDP套接字已手动关闭", style="yellow")
            except Exception as e:
                console.print(f"[DEBUG] 关闭UDP套接字时出错: {e}", style="red")
        AndroidClients.udp_socket = None

# 处理来自Android客户端的WebSocket连接
async def handle_android_websocket(websocket, path):
    """处理单个Android客户端的WebSocket连接"""
    client_addr = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    client_id = f"android_{int(time.time())}_{websocket.remote_address[0]}_{websocket.remote_address[1]}"
    
    console.print(f"[DEBUG] 新的Android WebSocket连接: {client_addr} (路径: {path})", style="green")
    
    # 注册客户端
    AndroidClients.add_client(client_id, websocket, client_addr)
    
    # 创建缓存对象，用于存储音频数据
    class ClientCache:
        def __init__(self):
            self.chunks = b""
            self.offset = 0
            self.frame_num = 0
    
    cache = ClientCache()
    console.print(f"[DEBUG] 已为客户端 {client_id} 创建音频缓存", style="cyan")
    
    try:
        async for message in websocket:
            try:
                # 解析JSON消息
                message_size = len(message)
                console.print(f"[DEBUG] 收到来自 {client_addr} 的消息，大小: {message_size} 字节", style="cyan")
                
                data = json.loads(message)
                
                # 处理音频数据
                if "data" in data:
                    # 解码Base64音频数据
                    encoded_size = len(data["data"])
                    audio_data = base64.b64decode(data["data"])
                    decoded_size = len(audio_data)
                    
                    console.print(f"[DEBUG] 收到音频数据: 编码大小={encoded_size}字节, 解码后={decoded_size}字节", style="cyan")
                    
                    cache.chunks += audio_data
                    cache.frame_num += len(audio_data)
                    
                    # 获取任务信息
                    task_id = data.get("task_id", client_id)
                    source = data.get("source", "android")
                    is_final = data.get("is_final", False)
                    seg_duration = data.get("seg_duration", 15)
                    seg_overlap = data.get("seg_overlap", 2)
                    seg_threshold = seg_duration + seg_overlap * 2
                    time_start = data.get("time_start", time.time())
                    
                    console.print(f"[DEBUG] 任务信息: ID={task_id}, 来源={source}, 是否最终={is_final}", style="cyan")
                    console.print(f"[DEBUG] 当前缓存: {len(cache.chunks)/4/16000:.2f}秒, 阈值: {seg_threshold}秒", style="cyan")
                    
                    # 处理音频数据，类似于WebSocket处理逻辑
                    if not is_final:
                        # 若缓冲已达到分段长度，将片段作为任务提交
                        while len(cache.chunks) / 4 / 16000 >= seg_threshold:
                            data_chunk = cache.chunks[: 4 * 16000 * (seg_duration + seg_overlap)]
                            cache.chunks = cache.chunks[4 * 16000 * seg_duration :]
                            
                            console.print(f"[DEBUG] 提交分段任务: 偏移={cache.offset}秒, 长度={len(data_chunk)/4/16000:.2f}秒", style="green")
                            
                            task = Task(
                                source=source,
                                data=data_chunk,
                                offset=cache.offset,
                                task_id=task_id,
                                socket_id=client_id,  # 使用客户端ID作为socket_id
                                overlap=seg_overlap,
                                is_final=False,
                                time_start=time_start,
                                time_submit=time.time(),
                            )
                            cache.offset += seg_duration
                            Cosmic.queue_in.put(task)
                            console.print(f"[DEBUG] 任务已提交到队列: ID={task_id}, 偏移={task.offset}秒", style="green")
                            
                    elif is_final:
                        # 客户端说片段结束，将缓冲区音频识别
                        console.print(f"[DEBUG] 收到最终标记，提交剩余缓存: {len(cache.chunks)/4/16000:.2f}秒", style="green")
                        
                        task = Task(
                            source=source,
                            data=cache.chunks[0:],
                            offset=cache.offset,
                            task_id=task_id,
                            socket_id=client_id,  # 使用客户端ID作为socket_id
                            overlap=seg_overlap,
                            is_final=True,
                            time_start=time_start,
                            time_submit=time.time(),
                        )
                        Cosmic.queue_in.put(task)
                        console.print(f"[DEBUG] 最终任务已提交到队列: ID={task_id}, 偏移={task.offset}秒", style="green")
                        
                        # 还原缓冲区、偏移时长
                        cache.chunks = b""
                        cache.offset = 0
                        cache.frame_num = 0
                        console.print(f"[DEBUG] 已重置客户端 {client_id} 的音频缓存", style="cyan")
                        
                        # 发送确认消息
                        response = {"status": "processing", "message": "音频数据已接收，正在处理"}
                        await websocket.send(json.dumps(response))
                        console.print(f"[DEBUG] 已发送处理确认消息到客户端 {client_addr}", style="green")
                        
            except json.JSONDecodeError:
                console.print(f"[DEBUG] 从客户端 {client_addr} 接收到无效的JSON数据", style="red")
            except Exception as e:
                console.print(f"[DEBUG] 处理客户端 {client_addr} 的消息时出错: {e}", style="red")
                
    except websockets.exceptions.ConnectionClosed as e:
        console.print(f"[DEBUG] 客户端连接断开: {client_addr}, 代码: {e.code}, 原因: {e.reason}", style="yellow")
    except Exception as e:
        console.print(f"[DEBUG] 处理客户端连接时出错: {e}", style="red")
    finally:
        # 移除客户端
        AndroidClients.remove_client(client_id)
        console.print(f"[DEBUG] 客户端 {client_id} 已从连接列表中移除", style="yellow")

# 发送识别结果给Android客户端
async def send_result_to_android_client(result):
    """将识别结果发送给Android客户端"""
    client_id = result.socket_id
    console.print(f"[DEBUG] 准备发送结果到Android客户端: {client_id}", style="cyan")
    
    client_info = AndroidClients.get_client(client_id)
    
    if not client_info:
        console.print(f"[DEBUG] 未找到客户端 {client_id}，无法发送结果", style="yellow")
        return
    
    websocket, client_addr = client_info
    
    # 构建响应消息
    response = {
        "task_id": result.task_id,
        "duration": result.duration,
        "time_start": result.time_start,
        "time_submit": result.time_submit,
        "time_complete": result.time_complete,
        "text": result.text,
        "is_final": result.is_final,
    }
    
    console.print(f"[DEBUG] 识别结果: 任务ID={result.task_id}, 文本长度={len(result.text)}, 是否最终={result.is_final}", style="cyan")
    
    # 发送响应
    try:
        await websocket.send(json.dumps(response))
        console.print(f"[DEBUG] 已成功发送结果到客户端 {client_addr}", style="green")
    except Exception as e:
        console.print(f"[DEBUG] 发送结果到Android客户端时出错: {e}", style="red")
        # 连接可能已断开，从客户端列表中移除
        AndroidClients.remove_client(client_id)
        console.print(f"[DEBUG] 已从列表中移除可能断开的客户端: {client_id}", style="yellow")

# 注意：WebSocket服务器将在主服务器中启动，不需要单独启动
# 在主服务器的WebSocket处理函数中，需要检查路径以区分Android客户端和普通客户端

# 启动Android连接服务
def start_android_connection_service():
    """启动Android连接服务，包括UDP广播监听"""
    # 注册退出时的清理函数
    atexit.register(AndroidClients.cleanup)
    
    # 启动UDP广播监听线程
    discovery_thread = threading.Thread(target=handle_discovery_requests, daemon=True)
    discovery_thread.start()
    
    console.print("Android连接服务已启动", style="green")
    
    # 只返回线程对象，不要尝试解包
    return discovery_thread
    
    # 在文件末尾添加
    # 确保函数可以被正确导入
    __all__ = ['start_android_connection_service', 'handle_android_websocket', 'send_result_to_android_client', 'AndroidClients']