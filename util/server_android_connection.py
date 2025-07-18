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
                    # 获取发送方的IP地址
                    client_ip = addr[0]
                    console.print(f"[DEBUG] 客户端IP地址: {client_ip}", style="cyan")
                    
                    # 获取本机所有网络接口（使用更可靠的方法）
                    lan_ip = None
                    
                    try:
                        # 方法1：尝试使用getaddrinfo获取网络接口
                        try:
                            hostname = socket.gethostname()
                            interfaces = socket.getaddrinfo(hostname, None)
                            
                            # 遍历所有接口，找到与客户端在同一网段的IP
                            for interface in interfaces:
                                ip = interface[4][0]
                                # 过滤IPv6地址和回环地址
                                if ':' not in ip and ip != '127.0.0.1':
                                    # 检查是否与客户端在同一网段
                                    if ip.split('.')[0:3] == client_ip.split('.')[0:3]:
                                        lan_ip = ip
                                        break
                            
                            # 如果没找到匹配的IP，使用第一个非本地IPv4地址
                            if not lan_ip:
                                for interface in interfaces:
                                    ip = interface[4][0]
                                    if ':' not in ip and ip != '127.0.0.1':
                                        lan_ip = ip
                                        break
                        except (socket.gaierror, OSError) as e:
                            console.print(f"[DEBUG] getaddrinfo失败: {e}，尝试备用方法", style="yellow")
                        
                        # 方法2：如果getaddrinfo失败，使用连接测试方法
                        if not lan_ip:
                            try:
                                # 创建一个临时socket连接到客户端，获取本地IP
                                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                                temp_socket.connect((client_ip, 80))
                                lan_ip = temp_socket.getsockname()[0]
                                temp_socket.close()
                                console.print(f"[DEBUG] 通过连接测试获取到本地IP: {lan_ip}", style="cyan")
                            except Exception as e:
                                console.print(f"[DEBUG] 连接测试方法失败: {e}", style="yellow")
                        
                        # 方法3：如果以上都失败，使用gethostbyname
                        if not lan_ip:
                            try:
                                lan_ip = socket.gethostbyname(socket.gethostname())
                                console.print(f"[DEBUG] 通过gethostbyname获取到IP: {lan_ip}", style="cyan")
                            except Exception as e:
                                console.print(f"[DEBUG] gethostbyname失败: {e}", style="yellow")
                        
                        # 方法4：最后的备用方案，使用配置中的地址
                        if not lan_ip:
                            if Config.addr != '0.0.0.0':
                                lan_ip = Config.addr
                                console.print(f"[DEBUG] 使用配置中的地址: {lan_ip}", style="cyan")
                            else:
                                lan_ip = '127.0.0.1'
                                console.print(f"[DEBUG] 使用默认回环地址: {lan_ip}", style="yellow")
                    
                    except Exception as e:
                        console.print(f"[DEBUG] 获取本地IP时出现未预期错误: {e}", style="red")
                        lan_ip = '127.0.0.1'
                    
                    # 构造响应
                    response = f"{lan_ip}:{WS_PORT}"
                    console.print(f"[DEBUG] 使用局域网IP地址: {lan_ip}", style="cyan")
                    udp_socket.sendto(response.encode('utf-8'), addr)
                    console.print(f"[DEBUG] 已回复发现请求: {response} 到 {addr}", style="green")
            except Exception as e:
                if isinstance(e, OSError) and e.errno == 9:  # Bad file descriptor
                    console.print("[DEBUG] UDP套接字已关闭，停止监听", style="yellow")
                    break
                console.print(f"[DEBUG] 处理UDP广播请求时出错: {e}", style="red")
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
            self.total_audio_size = 0
            self.total_packets = 0
            self.valid_packets = 0
            self.invalid_packets = 0
            self.recognition_results = []
    
    cache = ClientCache()
    console.print(f"[DEBUG] 已为客户端 {client_id} 创建音频缓存", style="cyan")
    
    # 启动结果接收协程
    async def receive_recognition_results():
        while True:
            try:
                # 从结果队列中获取识别结果
                console.print(f"[DEBUG] 等待识别结果...", style="cyan")
                result = await asyncio.to_thread(Cosmic.queue_out.get)
                if result is None:
                    console.print(f"[DEBUG] 收到空结果，退出接收循环", style="yellow")
                    break
                
                console.print(f"[DEBUG] 收到原始识别结果: {result}", style="cyan")
                console.print(f"[DEBUG] 当前客户端ID: {client_id}", style="cyan")
                console.print(f"[DEBUG] 结果客户端ID: {result.socket_id}", style="cyan")
                
                # 检查结果是否属于当前客户端
                if result.socket_id == client_id:
                    # 保存识别结果
                    cache.recognition_results.append(result)
                    
                    # 打印识别结果，使用更醒目的格式
                    console.print("\n" + "="*50, style="bold cyan")
                    console.print("[bold green]📝 语音识别结果[/bold green]")
                    console.print("="*50, style="bold cyan")
                    
                    # 基本信息
                    console.print(f"[bold cyan]任务信息:[/bold cyan]")
                    console.print(f"  📌 任务ID: [yellow]{result.task_id}[/yellow]")
                    console.print(f"  🕒 开始时间: [yellow]{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.time_start))}[/yellow]")
                    console.print(f"  ⏱️ 处理耗时: [yellow]{result.time_complete - result.time_start:.2f}秒[/yellow]")
                    
                    # 音频信息
                    console.print(f"\n[bold cyan]音频信息:[/bold cyan]")
                    console.print(f"  📊 音频时长: [yellow]{result.duration:.2f}秒[/yellow]")
                    if hasattr(result, 'tokens'):
                        console.print(f"  🔤 识别词数: [yellow]{len(result.tokens)}个词[/yellow]")
                    
                    # 识别结果
                    console.print(f"\n[bold cyan]识别内容:[/bold cyan]")
                    console.print(f"  [green]{result.text}[/green]")
                    
                    # 状态信息
                    console.print(f"\n[bold cyan]状态信息:[/bold cyan]")
                    console.print(f"  🏁 是否最终结果: [{'green' if result.is_final else 'yellow'}]{result.is_final}[/{'green' if result.is_final else 'yellow'}]")
                    
                    console.print("="*50 + "\n", style="bold cyan")
                    
                    # 发送识别结果给客户端
                    response = {
                        "type": "recognition_result",
                        "task_id": result.task_id,
                        "text": result.text,
                        "duration": result.duration,
                        "is_final": result.is_final,
                        "time_start": result.time_start,
                        "time_complete": result.time_complete,
                        "process_time": result.time_complete - result.time_start
                    }
                    await websocket.send(json.dumps(response))
                    console.print(f"[green]✅ 已发送识别结果到客户端 {client_addr}[/green]")
                else:
                    console.print(f"[DEBUG] 结果不属于当前客户端，跳过", style="yellow")
            
            except Exception as e:
                console.print(f"[red]❌ 处理识别结果时出错: {e}[/red]")
                console.print(f"[red]错误详情: {str(e)}[/red]")
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
    
    # 启动结果接收任务（修复拼写错误：oesult_task -> result_task）
    result_task = asyncio.create_task(receive_recognition_results())
    console.print(f"[DEBUG] 已启动识别结果接收任务", style="green")
    
    try:
        async for message in websocket:
            try:
                # 解析JSON消息
                message_size = len(message)
                console.print(f"[DEBUG] 收到来自 {client_addr} 的消息，大小: {message_size} 字节", style="cyan")
                
                data = json.loads(message)
                cache.total_packets += 1
                
                # 打印原始数据包信息
                console.print(f"[DEBUG] 数据包 #{cache.total_packets}:", style="cyan")
                console.print(f"[DEBUG] - 任务ID: {data.get('task_id', 'unknown')}", style="cyan")
                console.print(f"[DEBUG] - 来源: {data.get('source', 'unknown')}", style="cyan")
                console.print(f"[DEBUG] - 是否最终包: {data.get('is_final', False)}", style="cyan")
                
                # 处理音频数据
                if "data" in data:
                    try:
                        # 解码Base64音频数据
                        encoded_size = len(data["data"])
                        audio_data = base64.b64decode(data["data"])
                        decoded_size = len(audio_data)
                        cache.total_audio_size += decoded_size
                        cache.valid_packets += 1
                        
                        console.print(f"[DEBUG] 音频数据验证:", style="cyan")
                        console.print(f"[DEBUG] - Base64编码大小: {encoded_size} 字节", style="cyan")
                        console.print(f"[DEBUG] - 解码后大小: {decoded_size} 字节", style="cyan")
                        console.print(f"[DEBUG] - 累计音频数据: {cache.total_audio_size/1024:.2f} KB", style="cyan")
                        console.print(f"[DEBUG] - 当前音频时长: {decoded_size/4/16000:.2f} 秒", style="cyan")
                        
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
                        
                        console.print(f"[DEBUG] 任务处理信息:", style="cyan")
                        console.print(f"[DEBUG] - 缓存音频长度: {len(cache.chunks)/4/16000:.2f} 秒", style="cyan")
                        console.print(f"[DEBUG] - 分段阈值: {seg_threshold} 秒", style="cyan")
                        
                        # 处理音频数据
                        if not is_final:
                            # 若缓冲已达到分段长度，将片段作为任务提交
                            while len(cache.chunks) / 4 / 16000 >= seg_threshold:
                                data_chunk = cache.chunks[: 4 * 16000 * (seg_duration + seg_overlap)]
                                cache.chunks = cache.chunks[4 * 16000 * seg_duration :]
                                
                                console.print(f"[DEBUG] 提交分段任务:", style="green")
                                console.print(f"[DEBUG] - 偏移: {cache.offset} 秒", style="green")
                                console.print(f"[DEBUG] - 分段长度: {len(data_chunk)/4/16000:.2f} 秒", style="green")
                                
                                task = Task(
                                    source=source,
                                    data=data_chunk,
                                    offset=cache.offset,
                                    task_id=task_id,
                                    socket_id=client_id,
                                    overlap=seg_overlap,
                                    is_final=False,
                                    time_start=time_start,
                                    time_submit=time.time(),
                                    samplerate=16000,
                                )
                                cache.offset += seg_duration
                                Cosmic.queue_in.put(task)
                                console.print(f"[DEBUG] 任务已提交到队列: ID={task_id}, 偏移={task.offset}秒", style="green")
                                
                                # 在提交任务后添加日志
                                console.print(f"[cyan]已提交音频进行识别，等待结果...[/cyan]")
                                
                        elif is_final:
                            # 客户端说片段结束，将缓冲区音频识别
                            console.print(f"[DEBUG] 收到最终标记，提交剩余缓存:", style="green")
                            console.print(f"[DEBUG] - 剩余音频长度: {len(cache.chunks)/4/16000:.2f} 秒", style="green")
                            
                            task = Task(
                                source=source,
                                data=cache.chunks[0:],
                                offset=cache.offset,
                                task_id=task_id,
                                socket_id=client_id,
                                overlap=seg_overlap,
                                is_final=True,
                                time_start=time_start,
                                time_submit=time.time(),
                                samplerate=16000,
                            )
                            Cosmic.queue_in.put(task)
                            console.print(f"[DEBUG] 最终任务已提交到队列: ID={task_id}, 偏移={task.offset}秒", style="green")
                            
                            # 还原缓冲区、偏移时长
                            cache.chunks = b""
                            cache.offset = 0
                            cache.frame_num = 0
                            console.print(f"[DEBUG] 已重置客户端 {client_id} 的音频缓存", style="cyan")
                            
                            # 发送确认消息
                            response = {
                                "status": "processing",
                                "message": "音频数据已接收，正在处理",
                                "stats": {
                                    "total_packets": cache.total_packets,
                                    "valid_packets": cache.valid_packets,
                                    "invalid_packets": cache.invalid_packets,
                                    "total_audio_size": cache.total_audio_size,
                                    "total_duration": cache.total_audio_size/4/16000
                                }
                            }
                            await websocket.send(json.dumps(response))
                            console.print(f"[DEBUG] 已发送处理确认消息到客户端 {client_addr}", style="green")
                            
                    except base64.binascii.Error as e:
                        cache.invalid_packets += 1
                        console.print(f"[DEBUG] Base64解码失败: {e}", style="red")
                        console.print(f"[DEBUG] 无效数据包统计: {cache.invalid_packets}/{cache.total_packets}", style="red")
                        
            except json.JSONDecodeError:
                cache.invalid_packets += 1
                console.print(f"[DEBUG] 从客户端 {client_addr} 接收到无效的JSON数据", style="red")
                console.print(f"[DEBUG] 无效数据包统计: {cache.invalid_packets}/{cache.total_packets}", style="red")
            except Exception as e:
                console.print(f"[DEBUG] 处理客户端 {client_addr} 的消息时出错: {e}", style="red")
                
    except websockets.exceptions.ConnectionClosed as e:
        console.print(f"[DEBUG] 客户端连接断开: {client_addr}, 代码: {e.code}, 原因: {e.reason}", style="yellow")
        console.print(f"[DEBUG] 连接统计:", style="yellow")
        console.print(f"[DEBUG] - 总数据包: {cache.total_packets}", style="yellow")
        console.print(f"[DEBUG] - 有效数据包: {cache.valid_packets}", style="yellow")
        console.print(f"[DEBUG] - 无效数据包: {cache.invalid_packets}", style="yellow")
        console.print(f"[DEBUG] - 总音频大小: {cache.total_audio_size/1024:.2f} KB", style="yellow")
        console.print(f"[DEBUG] - 总音频时长: {cache.total_audio_size/4/16000:.2f} 秒", style="yellow")
        console.print(f"[DEBUG] - 识别结果数量: {len(cache.recognition_results)}", style="yellow")
    finally:
        # 取消结果接收任务
        result_task.cancel()
        try:
            await result_task
        except asyncio.CancelledError:
            pass
        
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
        "type": "recognition_result",
        "task_id": result.task_id,
        "text": result.text,
        "duration": result.duration,
        "is_final": result.is_final,
        "time_start": result.time_start,
        "time_complete": result.time_complete
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

    # 获取所有网络接口的IP地址（使用更可靠的方法）
    def get_all_ip_addresses():
        ip_list = []
        try:
            # 方法1：尝试使用getaddrinfo
            try:
                hostname = socket.gethostname()
                interfaces = socket.getaddrinfo(hostname, None)
                for interface in interfaces:
                    ip = interface[4][0]
                    # 过滤掉IPv6地址和回环地址
                    if ':' not in ip and ip != '127.0.0.1':
                        ip_list.append(ip)
            except (socket.gaierror, OSError) as e:
                console.print(f"[DEBUG] getaddrinfo在获取IP列表时失败: {e}，尝试备用方法", style="yellow")
            
            # 方法2：如果getaddrinfo失败，使用netifaces或其他方法
            if not ip_list:
                try:
                    import netifaces
                    for interface in netifaces.interfaces():
                        addrs = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addrs:
                            for addr in addrs[netifaces.AF_INET]:
                                ip = addr['addr']
                                if ip != '127.0.0.1':
                                    ip_list.append(ip)
                except ImportError:
                    console.print(f"[DEBUG] netifaces模块未安装，跳过此方法", style="yellow")
                except Exception as e:
                    console.print(f"[DEBUG] netifaces方法失败: {e}", style="yellow")
            
            # 方法3：使用socket连接测试方法
            if not ip_list:
                try:
                    # 连接到一个外部地址来获取本地IP
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    temp_socket.connect(("8.8.8.8", 80))
                    local_ip = temp_socket.getsockname()[0]
                    temp_socket.close()
                    if local_ip != '127.0.0.1':
                        ip_list.append(local_ip)
                    console.print(f"[DEBUG] 通过连接测试获取到IP: {local_ip}", style="cyan")
                except Exception as e:
                    console.print(f"[DEBUG] 连接测试方法失败: {e}", style="yellow")
            
            # 方法4：使用配置中的地址作为备用
            if not ip_list and Config.addr != '0.0.0.0':
                ip_list.append(Config.addr)
                console.print(f"[DEBUG] 使用配置中的地址: {Config.addr}", style="cyan")
        
        except Exception as e:
            console.print(f"[DEBUG] 获取IP地址列表时出现未预期错误: {e}", style="red")
        
        return list(set(ip_list)) if ip_list else ['127.0.0.1']  # 去重，如果没有找到任何IP则返回回环地址

    # 打印所有局域网IP地址
    try:
        ip_addresses = get_all_ip_addresses()
        console.print("\n[bold green]可用的局域网IP地址:")
        for ip in ip_addresses:
            console.print(f"[cyan]http://{ip}:{WS_PORT}[/cyan]")
        console.print()  # 空行

        # 打印主机名对应的IP（使用安全的方法）
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            console.print(f"[bold green]主机名解析IP地址: [cyan]http://{local_ip}:{WS_PORT}[/cyan]\n")
        except (socket.gaierror, OSError) as e:
            console.print(f"[DEBUG] 主机名解析失败: {e}，使用第一个可用IP地址", style="yellow")
            if ip_addresses:
                console.print(f"[bold green]使用第一个可用IP地址: [cyan]http://{ip_addresses[0]}:{WS_PORT}[/cyan]\n")
    except Exception as e:
        console.print(f"[DEBUG] 打印IP地址信息时出错: {e}", style="red")
        console.print(f"[bold green]使用默认地址: [cyan]http://127.0.0.1:{WS_PORT}[/cyan]\n")
    
    # 只返回线程对象，不要尝试解包
    return discovery_thread
    
    # 在文件末尾添加
    # 确保函数可以被正确导入
    __all__ = ['start_android_connection_service', 'handle_android_websocket', 'send_result_to_android_client', 'AndroidClients']


class ClientCache:
    def __init__(self):
        self.chunks = b""
        self.offset = 0
        self.frame_num = 0
        self.total_audio_size = 0
        self.total_packets = 0
        self.valid_packets = 0
        self.invalid_packets = 0

    def handle_android_websocket(self, data):
        console.print(f"[DEBUG] 数据包 #{self.total_packets}:", style="cyan")
        console.print(f"[DEBUG] - 任务ID: {data.get('task_id', 'unknown')}", style="cyan")
        console.print(f"[DEBUG] - 来源: {data.get('source', 'unknown')}", style="cyan")
        console.print(f"[DEBUG] - 是否最终包: {data.get('is_final', False)}", style="cyan")

        # 解码Base64音频数据
        try:
            encoded_size = len(data["data"])
            audio_data = base64.b64decode(data["data"])
            decoded_size = len(audio_data)
            self.total_audio_size += decoded_size
            self.valid_packets += 1

            console.print(f"[DEBUG] 音频数据验证:", style="cyan")
            console.print(f"[DEBUG] - Base64编码大小: {encoded_size} 字节", style="cyan")
            console.print(f"[DEBUG] - 解码后大小: {decoded_size} 字节", style="cyan")
            console.print(f"[DEBUG] - 累计音频数据: {self.total_audio_size/1024:.2f} KB", style="cyan")
            console.print(f"[DEBUG] - 当前音频时长: {decoded_size/4/16000:.2f} 秒", style="cyan")
        except base64.binascii.Error as e:
            self.invalid_packets += 1
            console.print(f"[DEBUG] Base64解码失败: {e}", style="red")
            console.print(f"[DEBUG] 无效数据包统计: {self.invalid_packets}/{self.total_packets}", style="red")

        console.print(f"[DEBUG] 音频数据验证:", style="cyan")
        console.print(f"[DEBUG] - Base64编码大小: {encoded_size} 字节", style="cyan")
        console.print(f"[DEBUG] - 解码后大小: {decoded_size} 字节", style="cyan")
        console.print(f"[DEBUG] - 累计音频数据: {self.total_audio_size/1024:.2f} KB", style="cyan")
        console.print(f"[DEBUG] - 当前音频时长: {decoded_size/4/16000:.2f} 秒", style="cyan")

        console.print(f"[DEBUG] 连接统计:", style="yellow")
        console.print(f"[DEBUG] - 总数据包: {self.total_packets}", style="yellow")
        console.print(f"[DEBUG] - 有效数据包: {self.valid_packets}", style="yellow")
        console.print(f"[DEBUG] - 无效数据包: {self.invalid_packets}", style="yellow")
        console.print(f"[DEBUG] - 总音频大小: {self.total_audio_size/1024:.2f} KB", style="yellow")
        console.print(f"[DEBUG] - 总音频时长: {self.total_audio_size/4/16000:.2f} 秒", style="yellow")

        response = {
            "status": "processing",
            "message": "音频数据已接收，正在处理",
            "stats": {
                "total_packets": self.total_packets,
                "valid_packets": self.valid_packets,
                "invalid_packets": self.invalid_packets,
                "total_audio_size": self.total_audio_size,
                "total_duration": self.total_audio_size/4/16000
            }
        }