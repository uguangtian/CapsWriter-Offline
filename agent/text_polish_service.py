# 文本润色服务

import asyncio
import json
import os
import time
import httpx
import websockets
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from util.config import LMStudioConfig, DoubaoConfig, DeepSeekConfig
from util.memory_monitor import cleanup_memory
from agent.agent_service import call_agent_service


class TextPolishService:
    """文本润色服务类
    
    提供统一的接口进行文本润色，支持不同的大模型服务商，如DeepSeek和豆包。
    支持长文本分段处理，并将结果写入文件。
    
    Attributes:
        model_type: 使用的模型类型，如'deepseek'或'doubao'
        output_dir: 输出文件的目录
        max_segment_length: 单次处理的最大文本长度
        overlap_length: 分段处理时的重叠长度
    """
    
    def __init__(self, 
                 model_type: str = 'deepseek', 
                 output_dir: str = "./polished",
                 max_segment_length: int = 4000, 
                 overlap_length: int = 100):
        """初始化文本润色服务
        
        Args:
            model_type: 使用的模型类型，支持'deepseek'和'doubao'
            output_dir: 输出文件的目录，默认为当前年月的文件夹
            max_segment_length: 单次处理的最大文本长度
            overlap_length: 分段处理时的重叠长度
        """
        self.model_type = model_type.lower()
        self.max_segment_length = max_segment_length
        self.overlap_length = overlap_length
        
        # 设置输出目录
        if output_dir is None:
            time_year = time.strftime("%Y", time.localtime())
            time_month = time.strftime("%m", time.localtime())
            self.output_dir = Path() / time_year / time_month / "polished"
        else:
            self.output_dir = Path(output_dir)
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def polish_text(self, text: str,agent="text_polish_lmstudio", action: str = "polish", 
                         output_filename: str = "./") -> Tuple[str, str]:
        from util.memory_monitor import cleanup_memory

        """润色文本并保存结果
        
        Args:
            text: 要润色的文本
            action: 操作类型，如'polish'(润色)、'summarize'(总结)等
            output_filename: 输出文件名，如果为None则自动生成
            
        Returns:
            Tuple[str, str]: (处理后的文本, 输出文件路径)
        """
        # 尝试导入内存监控模块
        try:
            from util.memory_monitor import cleanup_memory
            memory_monitor_available = True
        except ImportError:
            memory_monitor_available = False
            
        # 检测语言，如果是英文，需要先润色再翻译
        is_english = self._is_english_text(text)
        

        # 分段处理长文本
        if len(text) > self.max_segment_length:
            segments = self._split_text(text)
            processed_segments = []
            
            # 估计总处理量
            total_segments = len(segments)
            console_width = 80
            print(f"总共需要处理 {total_segments} 个段落")
            print("[" + "-" * console_width + "]")
            
            for i, segment in enumerate(segments):
                # 显示进度条
                progress = int((i / total_segments) * console_width)
                print(f"\r[{'#' * progress}{' ' * (console_width - progress)}] {i+1}/{total_segments}", end="")
                print(f"\n处理段落 {i+1}/{total_segments}，长度: {len(segment)}")
                
                if is_english:
                    # 英文文本先润色
                    print(f"开始处理段落1 {i+1}/{total_segments}，长度: {len(segment)}")
                    polished,_ = await call_agent_service(segment, agent, action=action)

                    # 再翻译成中文
                    print(f"开始处理段落2 {i+1}/{total_segments}，长度: {len(segment)}")
                    action="translate"
                    processed,_ = await call_agent_service(polished, agent, action)
                else:
                    # 中文文本直接润色
                    print(f"开始处理段落3 {i+1}/{total_segments}，长度: {len(segment)}")
                    processed,_ = await call_agent_service(segment, agent, action)
                    
                processed_segments.append(processed)
                
                # 每处理3个段落执行一次内存清理
                if memory_monitor_available and (i + 1) % 3 == 0:

                    await asyncio.to_thread(cleanup_memory)
                    
                # 释放不需要的变量
                if 'polished' in locals():
                    del polished

            # 合并处理后的段落
            result = self._merge_segments(processed_segments)
            
            # 处理完成后执行一次内存清理
            if memory_monitor_available:
                await asyncio.to_thread(cleanup_memory)
        else:
            # 短文本直接处理
            if is_english:
                # 英文文本先润色
                print(f"开始处理段落4，长度: {len(text)}")
                polished= await call_agent_service(text, agent, action=action)

                # 再翻译成中文
                print(f"开始处理段落5，长度: {len(text)}")
                action="translate"

                result= await call_agent_service(polished,agent, action)
            else:
                # 中文文本直接润色
                print(f"开始处理段落6，长度: {len(text)}")
                result,_ = await call_agent_service(text, action)
        
        # 保存结果到文件
        file_path = self._save_to_file(result, output_filename)
        
        return result, str(file_path)
    

    
    async def _translate_to_chinese(self, text: str) -> str:
        """将英文文本翻译成中文
        
        使用离线翻译服务将英文文本翻译成中文
        
        Args:
            text: 要翻译的英文文本
            
        Returns:
            str: 翻译后的中文文本
        """
        try:
            # 设置要发送的数据
            data = {"text": text}
            # 将Python字典转换为JSON格式的字符串
            json_data = json.dumps(data)
            
            # 使用WebSocket连接离线翻译服务
            url = f"ws://{ClientConfig.addr}:{ClientConfig.offline_translate_port}"
            async with websockets.connect(url) as ws:
                await ws.send(json_data)
                response = await ws.recv()
                # 解析JSON响应
                response_data = json.loads(response)
                # 返回翻译结果
                return response_data.get("translated_text", "翻译失败")
        except Exception as e:
            return f"翻译失败: {str(e)}"
    
    def _is_english_text(self, text: str) -> bool:
        """判断文本是否为英文
        
        通过检查文本中英文字符的比例来判断
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 如果文本主要是英文则返回True，否则返回False
        """
        # 移除空白字符
        text = text.strip()
        if not text:
            return False

        # 计算英文字符的数量
        english_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        # 计算文本的总长度
        total_chars = len(text)
        
        # 如果英文字符占比超过50%，则认为是英文文本
        return english_chars / total_chars > 0.5
    
    def _split_text(self, text: str) -> List[str]:
        """将长文本分割成多个段落
        
        Args:
            text: 要分割的长文本
            
        Returns:
            List[str]: 分割后的段落列表
        """
        segments = []
        start = 0
        
        while start < len(text):
            # 计算当前段落的结束位置
            end = min(start + self.max_segment_length, len(text))
            
            # 如果不是最后一个段落，尝试在句子边界处分割
            if end < len(text):
                # 尝试在句号、问号、感叹号后分割
                for i in range(end, max(end - self.overlap_length, start), -1):
                    if i < len(text) and text[i-1] in ['.', '。', '?', '？', '!', '！']:
                        end = i
                        break
            
            # 添加当前段落
            segments.append(text[start:end])
            
            # 更新下一个段落的起始位置
            start = end
        
        return segments
    
    def _merge_segments(self, segments: List[str]) -> str:
        """合并处理后的段落
        
        Args:
            segments: 处理后的段落列表
            
        Returns:
            str: 合并后的文本
        """
        return '\n'.join(segments)
    
    async def process_file(self, file_path: Union[str, Path], action: str = "translate") -> Tuple[str, str]:
        """处理文本文件并进行翻译
        
        Args:
            file_path: 要处理的文本文件路径
            action: 操作类型，如'translate'(翻译)
            
        Returns:
            Tuple[str, str]: (处理后的文本, 输出文件路径)
        """
        try:
            # 确保file_path是Path对象
            if isinstance(file_path, str):
                file_path = Path(file_path)
                
            # 检查文件是否存在
            if not file_path.exists():
                return f"文件不存在: {file_path}", ""
                
            # 读取文件内容
            try:
                text = file_path.read_text(encoding='utf-8')
            except Exception as e:
                return f"读取文件失败: {str(e)}", ""
            
            # 调用现有处理逻辑
            # 确保text是字符串类型
            if isinstance(text, dict):
                text = str(text)
            result, _ = await self.polish_text(text, action=action)

            # 生成新文件名（原文件路径+原文件名+处理类型+时间戳）
            orig_name = file_path.stem
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            new_filename = f"{orig_name}_{action}_{timestamp}.txt"
            
            # 在原文件所在目录创建结果文件
            output_file = file_path.parent / new_filename
            output_file.write_text(result, encoding='utf-8')
            
            print(f"文本已保存到: {output_file}")
            return result, str(output_file)
            
        except Exception as e:
            error_msg = f"文件处理失败: {str(e)}"
            print(error_msg)
            return error_msg, ""

    def _save_to_file(self, text: str, filename: str = "") -> Path:
        """将处理后的文本保存到文件
        
        Args:
            text: 要保存的文本
            filename: 文件名，如果为None则自动生成
            
        Returns:
            Path: 保存的文件路径
        """
        # 如果没有提供文件名，则使用时间戳生成一个
        if filename is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            action_type = "polished"
            return timestamp+action_type+".txt"
        
        # 确保文件名有.txt后缀
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # 构建完整的文件路径
        file_path = self.output_dir / filename
        
        # 写入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as e:
            print(f"保存文件时出错: {str(e)}","路径:",file_path)
            return file_path
        
        print(f"文本已保存到: {file_path}")
        return file_path