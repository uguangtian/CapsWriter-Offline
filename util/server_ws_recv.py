import json
import time
import base64
import asyncio
import websockets
from base64 import b64decode

from util.server_cosmic import console, Cosmic
from util.server_classes import Task, Result
from util.my_status import Status

status_mic = Status("正在接收音频", spinner="point")


class Cache:
    # 定义一个可变对象，用于保存音频数据、偏移时间
    def __init__(self):
        self.chunks = b""
        self.offset = 0
        self.frame_num = 0


async def message_handler(websocket, message, cache: Cache):
    """处理得到的音频流数据"""

    queue_in = Cosmic.queue_in

    # 声明使用全局的状态指示器变量
    global status_mic
    # 从消息中获取音频来源（麦克风或文件）
    source = message["source"]
    # 获取是否为最后一段音频的标志
    is_final = message["is_final"]
    # 判断是否为第一段音频（通过检查缓存是否为空）
    is_start = not bool(cache.chunks)

    # 获取 id
    task_id = message["task_id"]
    socket_id = str(websocket.id)

    # 获取分段长度（以多长的音频进行识别）
    seg_duration = message["seg_duration"]
    seg_overlap = message["seg_overlap"]
    seg_threshold = seg_duration + seg_overlap * 2

    # base64 解码音频数据，再
    # 音频数据是 float32、单声道、16000采样率
    data = b64decode(message["data"])
    cache.chunks += data
    cache.frame_num += len(data)

    if not is_final:
        # 打印消息
        if source == "mic":
            status_mic.start()
        if source == "file" and is_start:
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
    seg_duration = 15
    seg_overlap = 2
    seg_threshold = seg_duration + seg_overlap * 2

    # 片段缓冲区、偏移时长
    cache = Cache()

    # 接收数据
    try:
        async for message in websocket:
            # json 解码字符串
            message = json.loads(message)
            # console.print(f"[DEBUG] 收到消息类型: {message.get('source', 'unknown')}", style="cyan")
            # 处理数据
            await message_handler(websocket, message, cache)

        console.print(
            "ConnectionClosed...",
        )
    except websockets.exceptions.ConnectionClosedError:
        console.print("ConnectionClosed...")
    except websockets.ConnectionClosed:
        console.print(
            "ConnectionClosed...",
        )
    except websockets.InvalidState:
        console.print("InvalidState...")
    except Exception as e:
        console.print(f"Exception: {e}", style="red")
        console.print(f"[DEBUG] 处理WebSocket连接时出错: {e}", style="red")
    finally:
        status_mic.stop()
        status_mic.on = False
        sockets.pop(str(websocket.id))
        sockets_id.remove(str(websocket.id))
        console.print(f"[DEBUG] WebSocket连接已关闭，ID: {websocket.id}", style="yellow")
