import signal
import time
from multiprocessing import Queue
from platform import system

from util.config import ModelPaths, ParaformerArgs, SenseVoiceArgs
from util.config import ServerConfig as Config
from util.empty_working_set import empty_current_working_set
from util.server_cosmic import console
import logging

import jieba
import sherpa_onnx

from util.server_recognize_paraformer import paraformerRecognize
from util.server_recognize_sensevoice import recognize


def disable_jieba_debug():
    # 关闭 jieba 的 debug
    jieba.setLogLevel(logging.INFO)


def init_recognizer(queue_in: Queue, queue_out: Queue, sockets_id):
    # 导入模块
    with console.status("载入模块中…", spinner="bouncingBall", spinner_style="yellow"):
        CT_Transformer = None
        if Config.model == "Paraformer":
            try:
                from funasr_onnx import CT_Transformer
            except ImportError as e:
                console.print(f"[yellow]警告: funasr_onnx 未安装，标点功能将被禁用, e: {e}")
                CT_Transformer = None
        disable_jieba_debug()

    console.print("[green4]模块加载完成", end="\n\n")

    # 载入语音模型
    console.print("[yellow]语音模型载入中，载入时长约 20 秒，请耐心等待...", end="\r")
    t1 = time.time()
    try:
        if Config.model == "Paraformer":
            # 打印模型路径信息以便调试
            paraformer_args = {
                key: value
                for key, value in ParaformerArgs.__dict__.items()
                if not key.startswith("_")
            }
            console.print(f"[yellow]尝试加载 Paraformer 模型，参数: {paraformer_args}")
            
            recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
                **paraformer_args
            )
        else:
            sense_voice_args = {
                key: value
                for key, value in SenseVoiceArgs.__dict__.items()
                if not key.startswith("_")
            }
            console.print(f"[yellow]尝试加载 SenseVoice 模型，参数: {sense_voice_args}")
            
            # 检查 sherpa_onnx 版本，确认是否支持 from_sense_voice 方法
            if hasattr(sherpa_onnx.OfflineRecognizer, 'from_sense_voice'):
                recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                    **sense_voice_args
                )
            else:
                # 如果不支持 from_sense_voice 方法，尝试使用通用构造函数
                console.print("[yellow]sherpa_onnx 不支持 from_sense_voice 方法，尝试使用通用构造函数")
                recognizer = sherpa_onnx.OfflineRecognizer(**sense_voice_args)
        
        console.print("[green4]语音模型载入完成", end="\n\n")
    except Exception as e:
        console.print(f"[red]模型加载失败: {str(e)}")
        # 检查模型文件是否存在
        import os
        if Config.model == "Paraformer":
            model_path = ParaformerArgs.paraformer
            if not os.path.exists(model_path):
                console.print(f"[red]模型文件不存在: {model_path}")
            else:
                console.print(f"[yellow]模型文件存在但加载失败，可能是文件损坏或格式不兼容")
        
        # 通知主进程加载失败
        queue_out.put(False)
        return

    if Config.model == "Paraformer":
        # 载入标点模型
        punc_model = None
        if Config.format_punc and CT_Transformer is not None:
            console.print(
                "[yellow]标点模型载入中，载入时长约 50 秒，请耐心等待...", end="\r"
            )
            try:
                punc_model = CT_Transformer(ModelPaths.punc_model_dir, quantize=True)
                console.print("[green4]标点模型载入完成", end="\n\n")
            except Exception as e:
                console.print(f"[yellow]标点模型加载失败: {e}，将跳过标点处理", end="\n\n")
                punc_model = None
        elif Config.format_punc and CT_Transformer is None:
            console.print("[yellow]funasr_onnx 不可用，跳过标点模型加载", end="\n\n")

    console.print(f"模型加载耗时 {time.time() - t1 :.2f}s", end="\n\n")

    # 清空物理内存工作集
    if system() == "Windows":
        empty_current_working_set()

    queue_out.put(True)  # 通知主进程加载完了

    while True:
        # 从队列中获取任务消息
        # 阻塞最多1秒，便于中断退出
        try:
            # 添加更详细的调试信息
            console.print(f"[DEBUG] 等待音频任务... 当前活跃连接数: {len(sockets_id)} 活跃连接ID列表:{list(sockets_id)}", style="cyan")
            
            # 检查队列是否为空
            if hasattr(queue_in, '_qsize'):
                queue_size = queue_in._qsize()
                console.print(f"[DEBUG] 队列当前大小: {queue_size}", style="cyan")
            
            task = queue_in.get(timeout=None)  # 增加超时时间到3秒
            console.print(f"[DEBUG] 成功获取音频任务! task_id: {task.task_id}, data_len: {len(task.data)}, socket_id: {task.socket_id}", style="green")

        except Exception as e:
            # 区分不同类型的异常
            if "timeout" in str(e).lower() or "empty" in str(e).lower() or "Empty" in {type(e).__name__}:
                console.print(f"[DEBUG] 队列 读取心跳，继续等待... ", style="dim")
            else:
                console.print(f"[ERROR] 接收音频任务异常: {e} 异常类型: {type(e).__name__}, name low:{str(e).lower()}", style="red")
            continue

        if task.socket_id not in sockets_id:  # 检查任务所属的连接是否存活
            console.print(f"[DEBUG] 任务所属连接已断开，跳过处理, task.socket_id: {task.socket_id}, sockets_id: {sockets_id}", style="yellow")
            continue

        if Config.model == "Paraformer":
            console.print("[DEBUG] 使用 Paraformer 模型处理音频", style="cyan")
            result = paraformerRecognize(recognizer, punc_model, task)  # 执行识别
        else:
            console.print(f"[DEBUG] 使用 {Config.model} 模型处理音频", style="cyan")
            result = recognize(recognizer, task)  # 执行识别
        if result is None or result.text is None or result.text == "":
            console.print(f"[DEBUG] 识别结果为空，跳过处理", style="yellow")
            continue
        queue_out.put(result)  # 返回结果
        console.print(f"[DEBUG] 识别完成，结果长度: {len(result.text)} 已将结果放入输出队列", style="green")

