import re
import time
import numpy as np
from collections import defaultdict
from typing import Dict, List

from util.chinese_itn import chinese_to_num
from util.config import ServerConfig as Config
from util.format_tools import adjust_space
from util.server_classes import Result, Task
from util.server_cosmic import Cosmic, console

# 使用字典缓存结果，避免频繁创建/销毁对象
results: Dict[str, Result] = {}

# 缓存标点模型的结果
punc_cache: Dict[str, str] = {}
PUNC_CACHE_SIZE = 1000

def format_text(text: str, punc_model) -> str:
    """格式化文本，添加标点符号并进行数字转换"""
    if not text:
        return text
        
    if Config.format_spell:
        text = adjust_space(text)
        
    if Config.format_punc and punc_model:
        # 检查缓存中是否已有结果
        cache_key = text
        if cache_key in punc_cache:
            text = punc_cache[cache_key]
        else:
            # print('start punc_result 01:')
            try:
                # print('start punc_result:')
                punc_result = punc_model(text)
                # print('punc_result:punc_result:', punc_result)
                # 处理标点模型返回的不同格式：列表或元组
                if punc_result:
                    if isinstance(punc_result, (list, tuple)) and len(punc_result) > 0:
                        # print('punc_result2:')
                        text = punc_result[0]  # 取第一个元素作为带标点的文本
                        # 更新缓存
                        if len(punc_cache) >= PUNC_CACHE_SIZE:
                            # 如果缓存已满，清除一半的旧条目
                            old_keys = list(punc_cache.keys())[:PUNC_CACHE_SIZE//2]
                            for k in old_keys:
                                punc_cache.pop(k)
                        punc_cache[cache_key] = text
                    elif isinstance(punc_result, str):
                        # 如果直接返回字符串
                        text = punc_result
                        punc_cache[cache_key] = text
                    else:
                        console.print(f"[yellow]标点模型返回值格式未知: {type(punc_result)}，跳过标点处理。[/yellow]")
                else:
                    console.print("[red]标点模型返回值为空，跳过标点处理。[/red]")
            except Exception as e:
                console.print(f"[red]标点模型处理出错：{e}，跳过标点处理。[/red]")
                
    if Config.format_num:
        text = chinese_to_num(text)
        
    if Config.format_spell:
        text = adjust_space(text)
        
    return text

def paraformerRecognize(recognizer, punc_model, task: Task) -> Result:
    """优化的语音识别处理函数"""
    try:
        # 添加调试日志
  
        console.print(f"[DEBUG] 开始处理识别任务: task_id={task.task_id}, is_final={task.is_final}")
        # 获取或创建结果容器
        if task.task_id  not in results:
             console.print(f"[DEBUG]  新任务, 创建新的结果容器: task_id={task.task_id}, is_final={task.is_final}")
             results[task.task_id] = Result(task.task_id, task.socket_id, task.source)
        result = results[task.task_id]
        # 高效处理音频数据
        samples = np.frombuffer(task.data, dtype=np.float32)
        # 新增：空音频防护，避免 ONNX Conv 输入维度为 0 的异常
        if len(samples) == 0:
            console.print(f"[DEBUG] 警告：空的音频数据，跳过解码")
            # 更新时间戳
            result.time_start = task.time_start
            result.time_submit = task.time_submit
            result.time_complete = time.time()
            # 如果是最终任务，标记完成并返回最终结果
            if task.is_final:
                result.is_final = True
                final_result = results.pop(task.task_id)
                console.print(f"[DEBUG] 完成最终处理（空音频）: task_id={task.task_id}, is_final=True")
                return final_result
            return result
            
        # 检查音频数据的有效性
        #if len(samples) == 0:
        #    console.print(f"[DEBUG] 警告：空的音频数据")
        #    return result
            
        # 检查音频数据的范围
        #max_amplitude = np.max(np.abs(samples))
        #if max_amplitude > 1.0:
        #    console.print(f"[DEBUG] 警告：音频数据振幅过大 ({max_amplitude})，进行归一化")
        #    samples = samples / max_amplitude
        #    
        duration = len(samples) / task.samplerate
        result.duration += duration - task.overlap
        if task.is_final:
            result.duration += task.overlap
            
        console.print(f"[DEBUG] 音频数据信息: samples={len(samples)}, duration={duration:.2f}s, total_duration={result.duration:.2f}s")

        # 创建识别流并处理
        stream = recognizer.create_stream()
        # 样本非空才送入波形（上面已防护空样本）
        stream.accept_waveform(task.samplerate, samples)
        try:
            recognizer.decode_stream(stream)
        except Exception as e:
            console.print(f"[red] 解码失败: {e}")
            # 优雅回退，避免因异常导致任务中断
            if task.is_final:
                result.is_final = True
                final_result = results.pop(task.task_id)
                console.print(f"[DEBUG] 最终包解码异常，返回空结果: task_id={task.task_id}")
                return final_result
            return result

        # 更新时间戳
        result.time_start = task.time_start
        result.time_submit = task.time_submit
        result.time_complete = time.time()
        
        processing_time = result.time_complete - result.time_submit
        console.print(f"[DEBUG] 处理时间: {processing_time:.2f}s")

        # 优化重复内容去除
        timestamps = stream.result.timestamps
        tokens = stream.result.tokens
        
        if not timestamps or not tokens:
            console.print(f"[DEBUG] 警告：没有识别结果")
            # 即使识别结果为空，也要正确设置is_final状态
            if task.is_final:
                result.is_final = True
                # 从缓存中移除结果
                final_result = results.pop(task.task_id)
                console.print(f"[DEBUG] 完成空结果的最终处理: task_id={task.task_id}, is_final=True")
                return final_result
            return result
            
        console.print(f"[DEBUG] 识别结果: tokens_count={len(tokens)}")
        
        if not task.is_final:
            # 计算重叠区域的边界，使用更精确的重叠处理
            start_idx = 0
            end_idx = len(timestamps)
            
            # 使用更精确的重叠区域计算
            overlap_time = task.overlap
            for i, ts in enumerate(timestamps):
                if ts >= overlap_time / 2:  # 使用 >= 确保不会错过边界点
                    start_idx = i
                    break
                    
            if not task.is_final:
                for i in range(len(timestamps)-1, -1, -1):
                    if timestamps[i] <= duration - overlap_time / 2:
                        end_idx = i + 1
                        break

            # 优化重复内容检测
            if result.tokens:
                # 增加重叠检查的范围和精度
                max_overlap_check = min(5, len(result.tokens))  # 增加到5个token的检查范围
                for i in range(max_overlap_check, 0, -1):
                    if result.tokens[-i:] == tokens[start_idx:start_idx+i]:
                        start_idx += i
                        console.print(f"[DEBUG] 检测到重复内容: {i} tokens")
                        break

            # 更新结果前检查索引的有效性
            if start_idx < end_idx:
                result.timestamps.extend(t + task.offset for t in timestamps[start_idx:end_idx])
                result.tokens.extend(tokens[start_idx:end_idx])
                console.print(f"[DEBUG] 更新非最终结果: new_tokens={len(tokens[start_idx:end_idx])}, total_tokens={len(result.tokens)}")
            else:
                console.print(f"[DEBUG] 警告：无有效的新token (start_idx={start_idx}, end_idx={end_idx})")
        else:
            # 最终结果，添加所有剩余内容
            result.timestamps.extend(t + task.offset for t in timestamps)
            result.tokens.extend(tokens)
            console.print(f"[DEBUG] 更新最终结果: new_tokens={len(tokens)}, total_tokens={len(result.tokens)}")

        # 合并token并格式化文本
        text = " ".join(result.tokens).replace("@@ ", "")
        text = re.sub("([^a-zA-Z0-9]) (?![a-zA-Z0-9])", r"\1", text)
        result.text = text
        
        console.print(f"[DEBUG] 当前文本结果: {text}")

        if task.is_final:
            # 格式化最终文本
            result.text = format_text(text, punc_model)
            result.is_final = True
            # 从缓存中移除结果
            final_result = results.pop(task.task_id)
            console.print(f"[DEBUG] 完成最终结果处理: task_id={task.task_id}, text={final_result.text}")
            return final_result

        return result
        
    except Exception as e:
        console.print(f"[red]识别处理出错: {str(e)}")
        console.print(f"[red]错误堆栈: {e.__traceback__}")
        raise
