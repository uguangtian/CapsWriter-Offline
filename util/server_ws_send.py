import json
import websockets

from util.asyncio_to_thread import to_thread
from util.server_classes import Result
from util.server_cosmic import Cosmic, console
from util.server_android_connection import send_result_to_android_client, AndroidClients


async def ws_send():
    queue_out = Cosmic.queue_out
    sockets = Cosmic.sockets

    while True:
        try:
            # 获取识别结果（从多进程队列）
            result: Result = await to_thread(queue_out.get)

            # 得到退出的通知
            if result is None:
                return

            # 构建消息
            message = {
                "task_id": result.task_id,
                "duration": result.duration,
                "time_start": result.time_start,
                "time_submit": result.time_submit,
                "time_complete": result.time_complete,
                "tokens": result.tokens,
                "timestamps": result.timestamps,
                "text": result.text,
                "is_final": result.is_final,
            }

            # 检查是否是Android客户端
            if result.socket_id.startswith("android_"):
                # 发送结果给Android客户端
                await send_result_to_android_client(result)
            else:
                # 获得 WebSocket - 修复ID匹配逻辑
                websocket = None
                for ws_id, ws in sockets.items():
                    if ws_id == result.socket_id:
                        websocket = ws
                        break

                if not websocket:
                    console.print(f"[DEBUG] 未找到socket_id为 {result.socket_id} 的WebSocket连接，跳过发送", style="yellow")
                    continue

                # 检查连接状态并发送消息
                try:
                    # 检查WebSocket连接是否仍然有效
                    if hasattr(websocket, 'state'):
                        if websocket.state.name != 'OPEN':
                            console.print(f"[DEBUG] WebSocket连接已关闭 (socket_id: {result.socket_id})，跳过发送", style="yellow")
                            continue
                    
                    # 发送消息
                    message_json = json.dumps(message)
                    await websocket.send(message_json)
                    console.print(f"[DEBUG] 成功发送结果到客户端 (socket_id: {result.socket_id})，任务ID: {result.task_id}, is_final: {result.is_final}", style="green")
                    
                except websockets.exceptions.ConnectionClosed as e:
                    console.print(f"[DEBUG] 发送时发现连接已断开 (socket_id: {result.socket_id}): {e}", style="yellow")
                    # 从sockets字典中移除已断开的连接
                    if result.socket_id in sockets:
                        del sockets[result.socket_id]
                        console.print(f"[DEBUG] 已从连接列表中移除断开的连接: {result.socket_id}", style="yellow")
                except (BrokenPipeError, OSError) as e:
                    console.print(f"[DEBUG] 发送消息时管道错误 (socket_id: {result.socket_id}): {e}", style="yellow")
                    if result.socket_id in sockets:
                        del sockets[result.socket_id]
                        console.print(f"[DEBUG] 已从连接列表中移除断开的连接: {result.socket_id}", style="yellow")
                except Exception as e:
                    console.print(f"[DEBUG] 发送消息时出错 (socket_id: {result.socket_id}): {e}", style="red")

            if result.source == "mic":
                console.print(f"识别结果：\n    [green]{result.text}")
            elif result.source == "file":
                console.print(f"    转录进度：{result.duration:.2f}s", end="\r")
                if result.is_final:
                    console.print("\n    [green]转录完成")
            elif result.source == "android":
                console.print(f"Android识别结果：\n    [green]{result.text}")

        except Exception as e:
            print(e)
