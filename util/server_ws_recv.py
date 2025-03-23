import json
import time
import base64
import asyncio
import websockets
import numpy as np
from base64 import b64decode
from collections import defaultdict

from util.server_cosmic import console, Cosmic
from util.server_classes import Task, Result
from util.my_status import Status

status_mic = Status("正在接收音频", spinner="point")
class Cache:
    # 定义一个可变对象，用于保存音频数据、偏移时间
    def __init__(self):
        self.chunks = b""  # b前缀表示这是一个bytes类型的空字符串，用于存储二进制数据
        self.offset = 0
        self.frame_num = 0


class AudioCache:
    def __init__(self):
        self.chunks = []  # 使用列表存储二进制数据块
        self.total_size = 0  # 总数据大小
        self.offset = 0
        self.frame_num = 0
        self.chunk_buffer = defaultdict(list)  # 用于存储分块传输的数据
        
    def add_chunk(self, data, chunk_index=None, total_chunks=None):
        """添加数据块，支持分块传输"""
        if chunk_index is not None and total_chunks is not None:
            # 处理分块数据
            self.chunk_buffer[chunk_index].append(data)
            
            # 检查是否所有块都已接收
            if len(self.chunk_buffer) == total_chunks:
                # 按顺序合并所有块
                complete_data = b''.join([b''.join(self.chunk_buffer[i]) 
                                        for i in range(total_chunks)])
                self.chunks.append(complete_data)
                self.total_size += len(complete_data)
                self.chunk_buffer.clear()
        else:
            # 处理普通数据
            self.chunks.append(data)
            self.total_size += len(data)
    
    def get_data(self, size=None):
        """获取指定大小的数据"""
        if not self.chunks:
            return b""
            
        if size is None:
            # 返回所有数据
            data = b''.join(self.chunks)
            self.chunks = []
            self.total_size = 0
            return data
            
        # 计算需要多少个块才能满足size
        total_data = b''.join(self.chunks)
        if len(total_data) <= size:
            self.chunks = []
            self.total_size = 0
            return total_data
            
        # 分割数据
        result = total_data[:size]
        remaining = total_data[size:]
        self.chunks = [remaining]
        self.total_size = len(remaining)
        return result
    
    def clear(self):
        """清空缓存"""
        self.chunks = []
        self.total_size = 0
        self.offset = 0
        self.frame_num = 0
        self.chunk_buffer.clear()

async def message_handler(websocket, message, cache: Cache):
    """处理得到的音频流数据"""
    queue_in = Cosmic.queue_in
    global status_mic
    print('message_handler 处理得到的音频')
    try:
        source = message["source"]
        is_final = message["is_final"]
        #is_start = cache.total_size == 0
         # 判断是否为第一段音频（通过检查缓存是否为空）
        is_start = not bool(cache.chunks)

        task_id = message["task_id"]
        socket_id = str(websocket.id)

        """
        seg_duration = 15  # 分片时长
        seg_overlap = 2    # 重叠时长
        """
        # 获取分段长度（以多长的音频进行识别）
        seg_duration = message["seg_duration"]
        seg_overlap = message["seg_overlap"]
        seg_threshold = seg_duration + seg_overlap * 2  # 总阈值
        
        # 添加调试日志
        console.print(f"[DEBUG] 接收到音频数据: task_id={task_id}, is_final={is_final}, data_size={len(message.get('data', ''))}")
        
        # base64解码音频数据
        #data = b64decode(message["data"]) if message["data"] else b""
        # base64 解码音频数据，再
        # 音频数据是 float32、单声道、16000采样率
        data = b64decode(message["data"])
        cache.chunks += data
        cache.frame_num += len(data)

        if not is_final:
            if source == "mic":
                status_mic.start()
            elif source == "file" and is_start:
                console.print("正在接收音频文件...")

            # 若缓冲已达到分段长度，将片段作为任务提交
            while len(cache.chunks) / 4 / 16000 >= seg_threshold:
                data = cache.chunks[: 4 * 16000 * (seg_duration + seg_overlap)]
                cache.chunks = cache.chunks[4 * 16000 * seg_duration :]
                task = Task(
                    source=message["source"],
                    data=data,
                    offset=cache.offset,
                    task_id=task_id,
                    socket_id=socket_id,
                    overlap=seg_overlap,
                    is_final=False,
                    time_start=message["time_start"],
                    time_submit=time.time(),
                )
                cache.offset += seg_duration
                queue_in.put(task)

        elif is_final:
            # 打印消息
            if source == "mic":
                status_mic.stop()
            elif source == "file":
                print(f"音频文件接收完毕，时长 {cache.frame_num / 16000 / 4:.2f}s")

            # 客户端说片段结束，将缓冲区音频识别
            task = Task(
                source=message["source"],
                data=cache.chunks[0:],
                offset=cache.offset,
                task_id=task_id,
                socket_id=socket_id,
                overlap=seg_overlap,
                is_final=True,
                time_start=message["time_start"],
                time_submit=time.time(),
            )
            queue_in.put(task)

            # 还原缓冲区、偏移时长
            cache.chunks = b""
            cache.offset = 0
            cache.frame_num = 0
            console.print(f"[DEBUG] 任务完成，清理缓存: task_id={task_id}")
            
    except Exception as e:
        console.print(f"[DEBUG] 处理音频数据时出错: {e}", style="yellow")
        console.print(f"[DEBUG] 错误堆栈: {e.__traceback__}", style="yellow")
        # 不要抛出异常，让连接继续保持

#async def message_handler(websocket, message, cache: AudioCache):
##async def message_handler(websocket, message, cache: Cache):
#    """处理得到的音频流数据"""
#    queue_in = Cosmic.queue_in
#    global status_mic
#
#    try:
#        source = message["source"]
#        is_final = message["is_final"]
#        is_start = cache.total_size == 0
#
#        task_id = message["task_id"]
#        socket_id = str(websocket.id)
#
#        """
#        seg_duration = 15  # 分片时长
#        seg_overlap = 2    # 重叠时长
#        """
#        # 获取分段长度（以多长的音频进行识别）
#        seg_duration = message["seg_duration"]
#        seg_overlap = message["seg_overlap"]
#        seg_threshold = seg_duration + seg_overlap * 2  # 总阈值
#        
#        # 处理分块数据
#        chunk_index = message.get("chunk_index")
#        total_chunks = message.get("total_chunks")
#        
#        # 添加调试日志
#        console.print(f"[DEBUG] 接收到音频数据: task_id={task_id}, is_final={is_final}, data_size={len(message.get('data', ''))}")
#        
#        # base64解码音频数据
#        data = b64decode(message["data"]) if message["data"] else b""
#        if data:
#            try:
#                #cache.add_chunk(data, chunk_index, total_chunks)
#                cache.add_chunk(data, None, None)
#                cache.frame_num += len(data)
#                console.print(f"[DEBUG] 添加数据到缓存: size={len(data)}, total_size={cache.total_size}, frame_num={cache.frame_num}")
#            except Exception as e:
#                console.print(f"[DEBUG] 添加数据到缓存失败: {e}", style="yellow")
#                return  # 继续处理下一条消息
#
#        if not is_final:
#            if source == "mic":
#                status_mic.start()
#            elif source == "file" and is_start:
#                console.print("正在接收音频文件...")
#
#            # 处理达到阈值的数据
#            samples_per_segment = int(16000 * seg_threshold)  # 每个分段的样本数
#            bytes_per_segment = samples_per_segment * 4  # 每个分段的字节数
#            console.print(f"[DEBUG] 检查缓存大小: current={cache.total_size}, threshold={bytes_per_segment}")
#            
#            while cache.total_size >= bytes_per_segment:
#                try:
#                    segment_samples = int(16000 * (seg_duration + seg_overlap))
#                    segment_bytes = segment_samples * 4
#                    data = cache.get_data(segment_bytes)
#                    console.print(f"[DEBUG] 处理音频段: size={len(data)}, offset={cache.offset}")
#                    
#                    task = Task(
#                        source=source,
#                        data=data,
#                        offset=cache.offset,
#                        task_id=task_id,
#                        socket_id=socket_id,
#                        overlap=seg_overlap,
#                        is_final=False,
#                        time_start=message["time_start"],
#                        time_submit=time.time(),
#                        samplerate=message.get("samplerate", 16000),
#                    )
#                    cache.offset += seg_duration
#                    console.print(f"[DEBUG] 提交任务到队列: task_id={task_id}, offset={cache.offset}")
#                    await queue_in.put(task)
#                except Exception as e:
#                    console.print(f"[DEBUG] 处理音频段失败: {e}", style="yellow")
#                    break  # 跳出循环，等待下一次处理
#
#        elif is_final:
#            if source == "mic":
#                status_mic.stop()
#            elif source == "file":
#                print(f"音频文件接收完毕，时长 {cache.frame_num / 16000 / 4:.2f}s")
#
#            # 处理剩余数据
#            remaining_data = cache.get_data()
#            if remaining_data:
#                try:
#                    console.print(f"[DEBUG] 处理最终音频段: size={len(remaining_data)}")
#                    task = Task(
#                        source=source,
#                        data=remaining_data,
#                        offset=cache.offset,
#                        task_id=task_id,
#                        socket_id=socket_id,
#                        overlap=seg_overlap,
#                        is_final=True,
#                        time_start=message["time_start"],
#                        time_submit=time.time(),
#                        samplerate=message.get("samplerate", 16000),
#                    )
#                    await queue_in.put(task)
#                    console.print(f"[DEBUG] 提交最终任务到队列: task_id={task_id}")
#                except Exception as e:
#                    console.print(f"[DEBUG] 处理最终音频段失败: {e}", style="yellow")
#
#            # 重置缓存
#            cache.clear()
#            console.print(f"[DEBUG] 任务完成，清理缓存: task_id={task_id}")
#            
#    except Exception as e:
#        console.print(f"[DEBUG] 处理音频数据时出错: {e}", style="yellow")
#        console.print(f"[DEBUG] 错误堆栈: {e.__traceback__}", style="yellow")
#        # 不要抛出异常，让连接继续保持
#

async def ws_recv(websocket):
    global status_mic

    # 获取WebSocket路径
    path = websocket.path if hasattr(websocket, 'path') else '/'
    console.print(f"[DEBUG] 新的WebSocket连接，路径: {path}", style="cyan")
    
    # 检查是否是Android客户端
    if path == '/android':
        console.print(f"[DEBUG] 检测到Android客户端连接", style="green")
        # 如果是Android客户端，使用专门的处理函数
        from util.server_android_connection import handle_android_websocket
        await handle_android_websocket(websocket, path)
        return

    # 登记 socket 到字典，以 socket id 字符串为索引
    sockets = Cosmic.sockets
    sockets_id = Cosmic.sockets_id
    sockets[str(websocket.id)] = websocket
    sockets_id.append(str(websocket.id))
    console.print(f"接客了：{websocket}\n", style="yellow")

    # 设定分段长度
    seg_duration = 5   # 减小分片时长到5秒
    seg_overlap = 1    # 减小重叠时长到1秒
    seg_threshold = seg_duration + seg_overlap * 2

    # 片段缓冲区、偏移时长
    #cache = AudioCache()
    cache = Cache()
    
    # 设置更长的ping超时时间（如果可能）
    if hasattr(websocket, 'ping_timeout'):
        websocket.ping_timeout = 300  # 设置为300秒
    
    # 创建心跳任务
    heartbeat_task = None
    
    # 音频参数
    SAMPLE_RATE = 16000  # 采样率
    BYTES_PER_SAMPLE = 4  # float32类型每个样本4字节
    
    # 心跳函数
    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(30)  # 减少心跳间隔到30秒
                try:
                    # 发送ping并等待pong响应
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=20)  # 增加超时时间到20秒
                    console.print(f"[DEBUG] 心跳成功: {websocket.id}", style="dim")
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                    console.print(f"[DEBUG] 心跳失败，连接可能已断开: {websocket.id}", style="yellow")
                    return  # 不要立即中断，让主循环处理断开
                except Exception as e:
                    console.print(f"[DEBUG] 心跳异常: {e}", style="yellow")
                    continue  # 继续尝试下一次心跳
        except Exception as e:
            console.print(f"[DEBUG] 心跳任务异常: {e}", style="red")

    # 接收数据
    try:
        # 启动心跳任务
        heartbeat_task = asyncio.create_task(heartbeat())
        
        async for message in websocket:
            try:
                # json 解码字符串
                message = json.loads(message)
                # 处理数据
                print('start message_handler 处理得到的音频')
                await message_handler(websocket, message, cache)
            except json.JSONDecodeError as e:
                console.print(f"[DEBUG] JSON解析错误: {e}", style="yellow")
                continue  # 继续处理下一条消息
            except Exception as e:
                console.print(f"[DEBUG] 消息处理错误: {e}", style="yellow")
                continue  # 继续处理下一条消息

        console.print(
            "ConnectionClosed1...",
        )
    except websockets.exceptions.ConnectionClosedError:
        console.print("ConnectionClosed2...")
    except websockets.ConnectionClosed:
        console.print(
            "ConnectionClosed3...",
        )
    except websockets.InvalidState:
        console.print("InvalidState...")
    except Exception as e:
        console.print(f"Exception: {e}", style="red")
        console.print(f"[DEBUG] 处理WebSocket连接时出错: {e}", style="red")
    finally:
        # 取消心跳任务
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
                
        status_mic.stop()
        status_mic.on = False
        sockets.pop(str(websocket.id))
        sockets_id.remove(str(websocket.id))
        console.print(f"[DEBUG] WebSocket连接已关闭，ID: {websocket.id}", style="yellow")
