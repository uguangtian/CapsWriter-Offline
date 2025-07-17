import asyncio
import base64
import json
import re
import sys
import time
import uuid
from pathlib import Path

import websockets

from util import srt_from_txt
from util.client_check_websocket import check_websocket
from util.client_cosmic import Cosmic, console
from util.client_hot_sub import hot_sub
from util.client_hot_update import observe_hot, update_hot_all
from util.config import ClientConfig as Config


async def transcribe_check(file: Path):
    # 检查连接
    if not await check_websocket():
        console.print("无法连接到服务端", style="bright_red")
        sys.exit()

    if not file.exists():
        console.print(f"文件不存在：{file}", style="bright_red")
        return False


async def transcribe_send(file: Path):
    # 获取连接
    websocket = Cosmic.websocket

    # 生成任务id
    task_id = str(uuid.uuid1())
    console.print(f"\n任务标识：{task_id}")
    console.print(f"    处理文件：{file}")

    # 获取音频数据，ffmpeg输出采样率16000，单声道，float32格式
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(file),
        "-f",
        "f32le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-",
    ]

    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    console.print("    正在提取音频", end="\r")
    
    # 导入内存监控模块
    try:
        from util.memory_monitor import cleanup_memory
    except ImportError:
        cleanup_memory = None
    
    # 使用流式处理而不是一次性读取全部数据
    # 估算文件大小和时长
    try:
        # 尝试获取文件大小来估算音频长度
        file_size = os.path.getsize(file)
        # 粗略估算音频时长（假设比特率为128kbps）
        estimated_duration = file_size / (128 * 1024 / 8)
        console.print(f"    估计音频长度：{estimated_duration:.2f}s")
    except Exception as e:
        console.print(f"    无法估算音频长度: {e}")
        estimated_duration = 0

    # 流式处理音频数据
    # 分块大小，例如60秒
    chunk_size = 16000 * 4 * 60  # 16000采样率，4字节每个样本，60秒
    buffer_size = 1024 * 1024  # 1MB 缓冲区
    
    time_start = time.time()
    total_bytes_read = 0
    current_chunk = bytearray()
    processed_duration = 0
    
    # 使用流式读取处理音频数据
    while True:
        # 读取一块数据
        chunk = await process.stdout.read(buffer_size)
        if not chunk:  # 没有更多数据
            break
            
        # 累计读取的字节数
        total_bytes_read += len(chunk)
        processed_duration = total_bytes_read / 4 / 16000
        
        # 添加到当前处理块
        current_chunk.extend(chunk)
        
        # 当累积的数据超过预设的块大小时处理
        while len(current_chunk) >= chunk_size:
            # 提取一个完整的处理块
            data_to_process = current_chunk[:chunk_size]
            current_chunk = current_chunk[chunk_size:]
            
            # 计算时间戳
            time_frame = time_start + ((total_bytes_read - len(current_chunk) - len(data_to_process)) / 4 / 16000)
            
            # 是否为最后一块
            is_final = False
            
            # 构建消息
            message = {
                "task_id": task_id,  # 任务ID
                "seg_duration": Config.file_seg_duration,  # 分段长度
                "seg_overlap": Config.file_seg_overlap,  # 分段重叠
                "is_final": is_final,  # 是否结束
                "time_start": time_start,  # 录音起始时间
                "time_frame": time_frame,  # 该帧时间
                "source": "file",  # 数据来源：从文件读的数据
                "data": base64.b64encode(bytes(data_to_process)).decode("utf-8"),
            }
            
            # 发送数据
            try:
                await websocket.send(json.dumps(message))
                console.print(f"    发送进度：{processed_duration:.2f}s", end="\r")
            except websockets.exceptions.ConnectionClosed as e:
                console.print(f"    连接断开，错误：{e}")
                # 处理连接断开的情况
                return
                
            # 执行内存清理
            if cleanup_memory and total_bytes_read > 10 * 1024 * 1024:  # 每处理10MB数据清理一次
                await asyncio.to_thread(cleanup_memory)
                
    # 处理最后剩余的数据
    if current_chunk:
        time_frame = time_start + ((total_bytes_read - len(current_chunk)) / 4 / 16000)
        message = {
            "task_id": task_id,
            "seg_duration": Config.file_seg_duration,
            "seg_overlap": Config.file_seg_overlap,
            "is_final": True,  # 最后一块
            "time_start": time_start,
            "time_frame": time_frame,
            "source": "file",
            "data": base64.b64encode(bytes(current_chunk)).decode("utf-8"),
        }
        
        try:
            await websocket.send(json.dumps(message))
            console.print(f"    发送进度：{processed_duration:.2f}s", end="\r")
        except websockets.exceptions.ConnectionClosed as e:
            console.print(f"    连接断开，错误：{e}")
            
    console.print(f"\n    音频处理完成，总长度：{processed_duration:.2f}s")

    # 等待ffmpeg进程结束
    await process.wait()


async def transcribe_recv(file: Path):
    # 更新热词
    print("transcribe_recv")
    update_hot_all()
    # 实时更新热词
    observer = observe_hot()

    # 获取连接
    websocket = Cosmic.websocket

    # 接收结果
    async for message in websocket:
        message = json.loads(message)
        console.print(f"    转录进度: {message['duration']:.2f}s", end="\r")
        if message["is_final"]:
            break

    # 解析结果
    text_merge = message["text"]
    # 热词替换
    text_merge = hot_sub(text_merge)
    # text_split = re.sub("[，。？]", "\n", text_merge)
    text_split = re.sub("([，。？])", r"\1\n", text_merge)
    timestamps = message["timestamps"]
    tokens = message["tokens"]

    # 得到文件名
    json_filename = Path(file).with_suffix(".json")
    txt_filename = Path(file).with_suffix(".txt")
    merge_filename = Path(file).with_suffix(".merge.txt")

    # 写入结果
    with open(merge_filename, "w", encoding="utf-8") as f:
        f.write(text_merge)
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(text_split)
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump({"timestamps": timestamps, "tokens": tokens}, f, ensure_ascii=False)
    srt_from_txt.one_task(txt_filename)

    process_duration = message["time_complete"] - message["time_start"]
    console.print(f"\033[K    处理耗时：{process_duration:.2f}s")
    # console.print(f"    识别结果：\n[green]{message['text']}")
    console.print(f"    识别结果：\n[green]{text_merge}")
