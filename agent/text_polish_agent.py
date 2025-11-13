# 文本润色智能体

import asyncio
import os
import time
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from .base_agent import BaseAgent


class TextPolishAgent(BaseAgent):
    """文本润色智能体
    
    提供文本润色、总结、翻译等功能，支持长文本分段处理。
    
    Attributes:
        name: 智能体名称
        description: 智能体描述
        model_type: 使用的模型类型
        config: 智能体配置
        output_dir: 输出文件的目录
        max_segment_length: 单次处理的最大文本长度
        overlap_length: 分段处理时的重叠长度
    """
    
    def __init__(self, 
                 name: str = "文本润色智能体",
                 description: str = "提供文本润色、总结、翻译等功能",
                 model_type: str = "deepseek",
                 config: Dict[str, Any] = {},
                 output_dir: str = "./polished",
                 max_segment_length: int = 40000, 
                 overlap_length: int = 100):
        """初始化文本润色智能体
        
        Args:
            name: 智能体名称
            description: 智能体描述
            model_type: 使用的模型类型，支持'deepseek'、'doubao'和'lmstudio'
            config: 智能体配置参数
            output_dir: 输出文件的目录
            max_segment_length: 单次处理的最大文本长度
            overlap_length: 分段处理时的重叠长度
        """
        super().__init__(name, description, model_type, config)
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
    
    async def process(self, text: str, action: str = "polish", **kwargs) -> str:
        """处理文本
        
        Args:
            text: 要处理的文本
            action: 操作类型，如'polish'(润色)、'summarize'(总结)等
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        # 检测语言，如果是英文，需要先润色再翻译
        is_english = self._is_english_text(text)
        
        # 分段处理长文本
        if len(text) > self.max_segment_length:
            segments = self._split_text(text)
            processed_segments = []
            
            # 估计总处理量
            total_segments = len(segments)
            print(f"总共需要处理 {total_segments} 个段落")
            
            for i, segment in enumerate(segments):
                print(f"处理段落 {i+1}/{total_segments}，长度: {len(segment)}")
                
                if is_english:
                    # 英文文本先润色
                    polished = await self.call_api(segment, action)
                    # 再翻译成中文
                    processed = await self.call_api(polished, "text_polish_lmstudio")
                else:
                    # 中文文本直接润色
                    processed = await self.call_api(segment, action)
                    
                processed_segments.append(processed)
            
            # 合并处理后的段落
            result = self._merge_segments(processed_segments)
        else:
            # 短文本直接处理
            if is_english:
                # 英文文本先润色
                polished = await self.call_api(text, action)
                # 再翻译成中文
                result = await self.call_api(polished, "text_polish_lmstudio")
            else:
                # 中文文本直接润色
                result = await self.call_api(text, action)
        
        # 如果需要保存到文件
        save_to_file = kwargs.get('save_to_file', False)
        output_filename = kwargs.get('output_filename', None)
        if save_to_file:
            file_path = self._save_to_file(result, output_filename)
            return result
        
        return result
    
    def _is_english_text(self, text: str) -> bool:
        """检测文本是否为英文
        
        Args:
            text: 要检测的文本
            
        Returns:
            bool: 如果文本主要是英文则返回True，否则返回False
        """
        # 简单判断：如果文本中英文字符数量超过总字符数的70%，则认为是英文文本
        english_char_count = sum(1 for char in text if 'a' <= char.lower() <= 'z')
        return english_char_count / len(text) > 0.7 if len(text) > 0 else False
    
    def _split_text(self, text: str) -> List[str]:
        """将长文本分割成多个段落
        
        Args:
            text: 要分割的文本
            
        Returns:
            List[str]: 分割后的段落列表
        """
        segments = []
        start = 0
        
        while start < len(text):
            end = min(start + self.max_segment_length, len(text))
            
            # 如果不是最后一段，尝试在句子边界处分割
            if end < len(text):
                # 尝试在句号、问号、感叹号后分割
                for i in range(end, max(end - self.overlap_length, start), -1):
                    if i < len(text) and text[i-1] in ['.', '。', '?', '？', '!', '！']:
                        end = i
                        break
            
            segments.append(text[start:end])
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
    
    def _save_to_file(self, text: str, filename: Optional[str] = None) -> Path:
        """将处理后的文本保存到文件
        
        Args:
            text: 要保存的文本
            filename: 文件名，如果为None则自动生成
            
        Returns:
            Path: 保存的文件路径
        """
        # 如果没有提供文件名，则自动生成
        if not filename or filename == "./":
            time_str = time.strftime("%Y%m%d-%H%M%S", time.localtime())
            # 使用文本的前20个字符作为文件名的一部分
            text_preview = text[:20].replace('\n', ' ').replace('\r', ' ')
            # 移除不允许在文件名中使用的字符
            for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                text_preview = text_preview.replace(char, '')
            filename = f"{time_str}-polished-{text_preview}.txt"
        
        # 确保文件名有.txt后缀
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # 构建完整的文件路径
        file_path = self.output_dir / filename
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"已保存到文件: {file_path}")
        return file_path