import asyncio
import base64
import json
import uuid
import time

import numpy as np
import websockets

from util.client_cosmic import Cosmic, console
from util.client_create_file import create_file
from util.client_finish_file import finish_file
from util.client_write_file import write_file
from util.config import ClientConfig as Config
from util.client_check_websocket import check_websocket

# 添加音频缓冲区大小常量
BUFFER_SIZE = 48000 * 1  # 1秒的音频数据，减少延迟
MAX_CHUNK_SIZE = 32 * 1024  # 32KB，适合WebSocket传输的大小

class AudioBuffer:
    def __init__(self):
        self.buffer = []
        self.total_duration = 0
        self.current_size = 0
        self.last_send_time = 0  # 添加最后发送时间记录

    def add_data(self, data):
        self.buffer.append(data)
        self.current_size += len(data)
        self.total_duration += len(data) / 48000

    def get_data(self):
        if not self.buffer:
            return None
        data = np.concatenate(self.buffer)
        self.buffer = []
        self.current_size = 0
        return data

    def clear(self):
        self.buffer = []
        self.current_size = 0
        self.total_duration = 0
        self.last_send_time = 0

async def send_message(message):
    # 发送数据
    if (Cosmic.websocket is None or 
        (hasattr(Cosmic.websocket, 'state') and Cosmic.websocket.state.name != 'OPEN') or
        (hasattr(Cosmic.websocket, 'closed') and Cosmic.websocket.closed)):
        if message["is_final"]:
            task_id = message["task_id"]
            if task_id in Cosmic.audio_files:
                Cosmic.audio_files.pop(task_id)
                console.print("    服务端未连接，无法发送\n")
            else:
                console.print(f"    无法找到任务ID：{task_id}，无法移除\n")
        return

    try:
        await Cosmic.websocket.send(json.dumps(message))
        """
        if len(message.get("data", "")) > MAX_CHUNK_SIZE:
            chunks = [message["data"][i:i+MAX_CHUNK_SIZE] 
                     for i in range(0, len(message["data"]), MAX_CHUNK_SIZE)]
            for i, chunk in enumerate(chunks):
                chunk_message = message.copy()
                chunk_message["data"] = chunk
                chunk_message["chunk_index"] = i
                chunk_message["total_chunks"] = len(chunks)
                await Cosmic.websocket.send(json.dumps(chunk_message))
        else:
            await Cosmic.websocket.send(json.dumps(message))
        """
    except (websockets.ConnectionClosedError, BrokenPipeError, OSError) as e:
        # 尝试重连一次后重试发送
        try:
            await check_websocket()
            if Cosmic.websocket and (not (hasattr(Cosmic.websocket, 'closed') and Cosmic.websocket.closed)):
                await Cosmic.websocket.send(json.dumps(message))
                return
        except Exception:
            pass
        console.print(f"[red]发送错误: {str(e)}")

        
   
async def send_audio():
    try:
        task_id = str(uuid.uuid1())
        time_start = 0
        #audio_buffer = AudioBuffer()
        cache = []  # 阈值前的缓存（短暂）
        session_buffer = []  # 会话级缓存，整个录音周期的所有片段
        any_data_sent = False  # 是否发送过中间音频数据
        duration = 0
        file_path, file = "", None
        #MIN_SEND_INTERVAL = 0.1  # 最小发送间隔（秒）

        while task := await Cosmic.queue_in.get():
            Cosmic.queue_in.task_done()
            
            # print('task, type:',task["type"])
            if task["type"] == "begin":
                time_start = task["time"]
                print(f"[Log] 录音开始 task_id: {task_id}")
                #continue
            elif task["type"] == "data":
                # 在阈值之前积攒音频数据
                if task["time"] - time_start < Config.threshold:
                    cache.append(task["data"])
                    session_buffer.append(task["data"])
                    print(f"[Log] 积攒音频数据, 当前缓存块数: {len(cache)}, 累计时长: {(task['time'] - time_start):.2f}s")
                    continue
                    #audio_buffer.add_data(task["data"])
                    #current_time = time.time()
                
                # 首先处理音频数据
                if cache:
                    data = np.concatenate(cache)
                    #cache = []
                    cache.clear()
                else:
                    data = task["data"]
                # 记录到会话缓存（用于在意外情况下补发最终数据）
                session_buffer.append(data)
                
                # 创建音频文件（如果需要）
                if Config.save_audio and not file_path:
                    file_path, file = create_file(data.shape[1], time_start)
                    Cosmic.audio_files[task_id] = file_path
                duration += len(data) / 48000    
                    # 保存音频
                if Config.save_audio:
                    write_file(file, data)
                #if (audio_buffer.current_size >= BUFFER_SIZE or 
                #    (current_time - audio_buffer.last_send_time >= MIN_SEND_INTERVAL and audio_buffer.current_size > 0)):
                if (True):
                    
                    #data = audio_buffer.get_data()
                    #audio_buffer.last_send_time = current_time
                    
                    
                    
                    # 优化：使用numpy的mean操作一次性处理
                    # 将48kHz降采样到16kHz，保持音频质量
                    # 1. 首先转换为float32类型进行处理
                    # data = data.astype(np.float32)
                    # 3. 从48kHz降采样到16kHz (每3个样本取1个)
                    #processed_data = data[::3]
                    # 2. 如果是立体声，转换为单声道
                    #if len(data.shape) > 1:
                    #    processed_data = np.mean(processed_data, axis=1)

                    
                    # 发送音频数据
                    encoded_data = base64.b64encode(  # 数据
                            np.mean(data[::3], axis=1).astype(np.float32).tobytes()
                        ).decode("utf-8")
                    
                    #print(f"[Log] 发送中间音频数据, 原始长度: {len(data)}, 编码后长度: {len(encoded_data)}")

                    message = {
                        "task_id": task_id,
                        "seg_duration": Config.mic_seg_duration,
                        "seg_overlap": Config.mic_seg_overlap,
                        "is_final": False,
                        "time_start": time_start,
                        "time_frame": task["time"],
                        "source": "mic",
                        #"data": base64.b64encode(processed_data.tobytes()).decode("utf-8"),
                        "data": encoded_data,
                        #"samplerate": 16000,
                    }
                    #await send_message(message)
                    task = asyncio.create_task(send_message(message))
                    any_data_sent = True

            #elif task["type"] in ["finish", "cancel"]:
                # print('case 1, type finish:',task_id)
            elif task["type"] == "finish":
                print(f"[Log] 录音结束, 开始处理 finish 任务, task_id: {task_id}")
                
                # 准备发送的数据
                final_data = ""
                
                # 处理剩余的缓存数据
                if cache:
                    data = np.concatenate(cache)
                    cache.clear()
                    print(f"[Log] finish 任务中处理剩余缓存数据, 原始长度: {len(data)}")
                    if Config.save_audio and file:
                        write_file(file, data)
                    
                    # 处理音频数据用于发送
                    try:
                        # 确保数据格式正确
                        if len(data.shape) > 1:
                            processed_data = np.mean(data[::3], axis=1)
                        else:
                            processed_data = data[::3]
                        
                        final_data = base64.b64encode(
                            processed_data.astype(np.float32).tobytes()
                        ).decode("utf-8")
                    except Exception as e:
                        console.print(f"[red]处理最终音频数据出错: {e}")
                # 若没有缓存、且整个会话期间从未发送过中间数据，则使用会话缓存补发
                if final_data == "" and not any_data_sent and session_buffer:
                    try:
                        session_audio = np.concatenate(session_buffer)
                        print(f"[Log] 使用会话缓存补发最终数据, 原始长度: {len(session_audio)}")
                        if len(session_audio.shape) > 1:
                            processed_session = np.mean(session_audio[::3], axis=1)
                        else:
                            processed_session = session_audio[::3]
                        final_data = base64.b64encode(
                            processed_session.astype(np.float32).tobytes()
                        ).decode("utf-8")
                    except Exception as e:
                        console.print(f"[red]补发最终数据时出错: {e}")

                elif Config.save_audio and file:
                    # 如果没有缓存数据但需要保存音频，确保文件正确关闭
                    pass
                
                # 发送最后的音频数据
                message = {
                    "task_id": task_id,
                    "seg_duration": Config.mic_seg_duration,
                    "seg_overlap": Config.mic_seg_overlap,
                    "is_final": True,
                    "time_start": time_start,
                    "time_frame": task["time"],
                    "source": "mic",
                    "data": final_data,  # 发送剩余数据
                }
                print(f"[Log] 发送 finish 消息, task_id: {task_id}, final_data 长度: {len(final_data)}")
                #await send_message(message)
                task = asyncio.create_task(send_message(message))
                break

                
               # if Config.save_audio:
               #     finish_file(file)
                
            elif task["type"] == "cancel":
            #console.print(f"任务标识：{task_id}")
            #console.print(f"    录音时长：{duration:.2f}s")
            #console.print(f"    录音时长：{audio_buffer.total_duration:.2f}s")
            
                # 发送结束消息
                message = {
                    "task_id": task_id,
                    "seg_duration": Config.mic_seg_duration,
                    "seg_overlap": Config.mic_seg_overlap,
                    "is_final": True,
                    "time_start": time_start,
                    "time_frame": task["time"],
                    "source": "mic",
                    "data": "",
                    #"samplerate": 16000,
                }
                #await send_message(message)
                task = asyncio.create_task(send_message(message))
                break
            else:
                print('case 3, type:',task["type"])
    except Exception as e:
        console.print(f"[red]错误: {str(e)}")
        console.print(f"[red]错误堆栈: {e.__traceback__}")  # 添加更详细的错误信息


# 新增键盘监听函数
def on_press(key):
    try:
        if key.char == 's':  # 按下 's' 键开始录音
            console.print("开始录音...")
            # 在这里添加开始录音的逻辑
        elif key.char == 'e':  # 按下 'e' 键结束录音
            console.print("结束录音...")
            # 在这里添加结束录音的逻辑
    except AttributeError:
        pass


def on_release(key):
    from pynput import keyboard as pynput_keyboard

    if key == pynput_keyboard.Key.esc:  # 按下 'esc' 键退出程序
        console.print("退出程序...")
        return False


# 启动键盘监听
def start_keyboard_listener():
    from pynput import keyboard as pynput_keyboard

    with pynput_keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


async def heartbeat():
    """客户端心跳处理"""
    try:
        while True:
            if (Cosmic.websocket and 
                not ((hasattr(Cosmic.websocket, 'state') and Cosmic.websocket.state.name != 'OPEN') or
                     (hasattr(Cosmic.websocket, 'closed') and Cosmic.websocket.closed))):
                try:
                    # 等待服务器的ping
                    pong_waiter = await Cosmic.websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=30)  # 增加超时时间到30秒
                    console.print(f"[DEBUG] 心跳成功", style="dim")
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                    console.print(f"[yellow]心跳失败，连接可能已断开[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[yellow]心跳异常: {e}[/yellow]")
            await asyncio.sleep(60)  # 增加心跳间隔到60秒，与服务端保持一致
    except Exception as e:
        console.print(f"[red]心跳任务异常: {e}[/red]")


# 主函数
if __name__ == "__main__":
    console.print("始监听按键")
    console.print("使用 pynput 监听键盘事件，无需管理员权限")
    console.print("连接服务端...  （服务端载入模块时长约 50 秒，请耐心等待。若好几分钟了还无响应 -> 服务端软件 start_server_gui.exe 启动了吗？ 服务端地址当前设置 127.0.0.1:6016 是正确的吗？）")
    console.print("连接成功")

    # 创建事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 启动心跳任务
    heartbeat_task = loop.create_task(heartbeat())

    try:
        # 启动键盘监听
        start_keyboard_listener()

        # 启动音频发送任务
        loop.run_until_complete(send_audio())
    finally:
        # 取消心跳任务
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                loop.run_until_complete(heartbeat_task)
            except asyncio.CancelledError:
                pass
        loop.close()
