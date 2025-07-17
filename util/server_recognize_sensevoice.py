import time

import numpy as np

from util.chinese_itn import chinese_to_num
from util.config import ServerConfig as Config
from util.format_tools import adjust_space
from util.server_classes import Result, Task
from rich import console

results = {}


def format_text(text):
    if Config.format_spell:
        text = adjust_space(text)  # 调空格
    if Config.format_num:
        text = chinese_to_num(text)  # 转数字
    if Config.format_spell:
        text = adjust_space(text)  # 调空格
    return text


def recognize(recognizer, task: Task):
    # inspect({key:value for key, value in task.__dict__.items() if not key.startswith('_') and key != 'data'})
    # todo 清空遗存的任务结果

    console.print(f"[DEBUG] 开始处理识别任务: ID={task.task_id}", style="cyan")

    # 确保结果容器存在
    if task.task_id not in results:
        results[task.task_id] = Result(task.task_id, task.socket_id, task.source)
        console.print(f"[DEBUG] 创建新的结果容器: ID={task.task_id}", style="cyan")

    # 取出结果容器
    result = results[task.task_id]

    # 片段预处理
    samples = np.frombuffer(task.data, dtype=np.float32)
    duration = len(samples) / task.samplerate
    result.duration += duration - task.overlap
    if task.is_final:
        result.duration += task.overlap
    
    console.print(f"[DEBUG] 音频片段信息:", style="cyan")
    console.print(f"[DEBUG] - 采样数: {len(samples)}", style="cyan")
    console.print(f"[DEBUG] - 时长: {duration:.2f}秒", style="cyan")
    console.print(f"[DEBUG] - 累计时长: {result.duration:.2f}秒", style="cyan")

    # 识别片段
    console.print(f"[DEBUG] 开始识别音频片段...", style="cyan")
    stream = recognizer.create_stream()
    stream.accept_waveform(task.samplerate, samples)
    recognizer.decode_stream(stream)
    console.print(f"[DEBUG] 音频片段识别完成", style="green")

    # 记录识别时间
    result.time_start = task.time_start
    result.time_submit = task.time_submit
    result.time_complete = time.time()
    
    console.print(f"[DEBUG] 处理时间信息:", style="cyan")
    console.print(f"[DEBUG] - 开始时间: {result.time_start}", style="cyan")
    console.print(f"[DEBUG] - 提交时间: {result.time_submit}", style="cyan")
    console.print(f"[DEBUG] - 完成时间: {result.time_complete}", style="cyan")
    console.print(f"[DEBUG] - 总耗时: {result.time_complete - result.time_start:.2f}秒", style="cyan")

    # 先粗去重，依据：字级时间戳
    m = n = len(stream.result.timestamps)
    for i, timestamp in enumerate(stream.result.timestamps, start=0):
        if timestamp > task.overlap / 2:
            m = i
            break
    for i, timestamp in enumerate(stream.result.timestamps, start=1):
        n = i
        if timestamp > duration - task.overlap / 2:
            break
    if not result.timestamps:
        m = 0
    if task.is_final:
        n = len(stream.result.timestamps)

    # 再细去重，依据：在端点是否有重复的字
    if result.tokens and result.tokens[-2:] == stream.result.tokens[m:n][:2]:
        m += 2
    elif result.tokens and result.tokens[-1:] == stream.result.tokens[m:n][:1]:
        m += 1

    # 最后与先前的结果合并
    result.timestamps += [t + task.offset for t in stream.result.timestamps[m:n]]
    result.tokens += [token for token in stream.result.tokens[m:n]]

    # token 合并为文本
    text = "".join(result.tokens)
    console.print(f"[DEBUG] 生成文本: {text}", style="green")

    result.text = text

    if not task.is_final:
        console.print(f"[DEBUG] 返回中间结果: {len(text)}字", style="cyan")
        return result

    # 调整文本格式
    result.text = format_text(text)
    console.print(f"[DEBUG] 格式化后的文本: {result.text}", style="green")

    # 若最后一个片段完成识别，从字典摘取任务
    result = results.pop(task.task_id)
    result.is_final = True
    console.print(f"[DEBUG] 任务完成，从结果字典中移除: ID={task.task_id}", style="green")

    return result
