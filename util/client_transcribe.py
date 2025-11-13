import asyncio
import base64
import json
import re
import sys
import time
import uuid
import os
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

    # 等待ffmpeg进程结束，添加超时控制
    try:
        await asyncio.wait_for(process.wait(), timeout=30.0)  # 30秒超时
        console.print(f"    ffmpeg进程正常结束")
    except asyncio.TimeoutError:
        console.print(f"    ffmpeg进程等待超时，强制终止")
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)  # 再等5秒
        except asyncio.TimeoutError:
            console.print(f"    ffmpeg进程强制终止失败，使用kill")
            process.kill()
            await process.wait()


async def transcribe_recv(file: Path, output_dir: Path = "~/Movies/Transcription"):
    """
    接收转录结果并保存到文件
    
    Args:
        file: 原始音频文件路径
        output_dir: 可选的输出目录路径，如果不指定则使用原文件所在目录
    """
    # 更新热词
    print("transcribe_recv")
    update_hot_all()
    # 实时更新热词
    observer = observe_hot()

    # 获取连接
    websocket = Cosmic.websocket

    # 接收结果
    message = None
    max_wait_time = 600  # 最大等待时间10分钟
    start_time = time.time()
    
    try:
        console.print(f"[DEBUG] 开始接收转录结果...", style="cyan")
        
        # 使用asyncio.wait_for为整个接收过程设置超时
        async def receive_results():
            nonlocal message
            async for msg in websocket:
                msg_data = json.loads(msg)
                console.print(f"[DEBUG] 收到消息: task_id={msg_data.get('task_id', 'unknown')}, is_final={msg_data.get('is_final', False)}, duration={msg_data.get('duration', 0):.2f}s", style="cyan")
                console.print(f"    转录进度: {msg_data['duration']:.2f}s", end="\r")
                if msg_data["is_final"]:
                    console.print(f"\n[DEBUG] 收到最终结果，文本长度: {len(msg_data.get('text', ''))}", style="green")
                    message = msg_data
                    break
                    
        await asyncio.wait_for(receive_results(), timeout=max_wait_time)
        
    except asyncio.TimeoutError:
        console.print(f"\n[ERROR] 接收转录结果超时（{max_wait_time}秒），可能转录任务失败", style="red")
        raise Exception(f"转录结果接收超时")
    except websockets.exceptions.ConnectionClosed as e:
        console.print(f"\n    接收结果时连接断开: {e}", style="yellow")
        # 尝试重新连接并继续接收
        if not await check_websocket():
            console.print("    无法重新连接到服务端", style="bright_red")
            raise
        websocket = Cosmic.websocket
        
        # 继续接收剩余结果，但设置较短的超时时间
        try:
            async def receive_remaining():
                nonlocal message
                async for msg in websocket:
                    msg_data = json.loads(msg)
                    console.print(f"    转录进度: {msg_data['duration']:.2f}s", end="\r")
                    if msg_data["is_final"]:
                        message = msg_data
                        break
                        
            remaining_time = max_wait_time - (time.time() - start_time)
            if remaining_time > 0:
                await asyncio.wait_for(receive_remaining(), timeout=remaining_time)
            else:
                raise Exception("总体接收时间已超时")
        except asyncio.TimeoutError:
            console.print(f"\n[ERROR] 重连后接收结果仍然超时", style="red")
            raise Exception("重连后转录结果接收超时")
    
    if message is None:
        raise Exception("未能接收到转录结果")

    # 解析结果
    text_merge = message["text"]
    # 热词替换
    text_merge = hot_sub(text_merge)
    # text_split = re.sub("[，。？]", "\n", text_merge)
    text_split = re.sub("([，。？])", r"\1\n", text_merge)
    timestamps = message["timestamps"]
    tokens = message["tokens"]

    # 确定输出目录和文件名
    if output_dir is not None:
        # 使用自定义输出目录
        output_dir = Path(output_dir)
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用原文件的基础名称，但放在指定的输出目录中
        base_name = Path(file).stem
        json_filename = output_dir / f"{base_name}.json"
        txt_filename = output_dir / f"{base_name}.txt"
        merge_filename = output_dir / f"{base_name}.merge.txt"
        srt_filename = output_dir / f"{base_name}.srt"
        
        console.print(f"    输出目录：{output_dir}")
    else:
        # 使用原文件所在目录（原有行为）
        json_filename = Path(file).with_suffix(".json")
        txt_filename = Path(file).with_suffix(".txt")
        merge_filename = Path(file).with_suffix(".merge.txt")
        srt_filename = Path(file).with_suffix(".srt")

    # 写入结果
    with open(merge_filename, "w", encoding="utf-8") as f:
        f.write(text_merge)
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(text_split)
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump({"timestamps": timestamps, "tokens": tokens}, f, ensure_ascii=False)
    
    # 生成SRT字幕文件
    srt_from_txt.one_task(txt_filename)
    
    # 如果使用了自定义输出目录，需要将生成的SRT文件移动到正确位置
    if output_dir is not None:
        original_srt = Path(file).with_suffix(".srt")
        if original_srt.exists():
            import shutil
            shutil.move(str(original_srt), str(srt_filename))
            console.print(f"    SRT文件已移动到：{srt_filename}")

    process_duration = message["time_complete"] - message["time_start"]
    console.print(f"\033[K    处理耗时：{process_duration:.2f}s")
    # console.print(f"    识别结果：\n[green]{message['text']}")
    console.print(f"    识别结果：\n[green]{text_merge}")
    
    # 输出文件保存信息
    console.print(f"    文件已保存：")
    console.print(f"      - 合并文本：{merge_filename}")
    console.print(f"      - 分段文本：{txt_filename}")
    console.print(f"      - 时间戳数据：{json_filename}")
    if output_dir is not None and srt_filename.exists():
        console.print(f"      - SRT字幕：{srt_filename}")
    elif Path(file).with_suffix(".srt").exists():
        console.print(f"      - SRT字幕：{Path(file).with_suffix('.srt')}")
