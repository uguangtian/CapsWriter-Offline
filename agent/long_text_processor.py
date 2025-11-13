#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长文本处理智能体
支持长文本的分段处理、总结、润色、纠错等功能
"""

import asyncio
import re
import math
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent


class LongTextProcessor(BaseAgent):
    """长文本处理智能体
    
    支持长文本的分段处理，包括总结、润色、纠错等功能。
    自动处理AI模型上下文长度限制问题。
    """
    
    def __init__(self, model_type: str = "deepseek", config: Dict[str, Any] = None):
        """初始化长文本处理智能体
        
        Args:
            model_type: 使用的模型类型
            config: 配置参数
        """
        default_config = {
            "max_tokens_per_segment": 40000,  # 每段最大token数
            "overlap_tokens": 200,  # 段落重叠token数
            "min_segment_length": 100,  # 最小段落长度
            "preserve_context": True,  # 是否保持上下文连贯性
        }
        
        if config:
            default_config.update(config)
            
        super().__init__(
            name="long_text_processor",
            description="长文本处理智能体，支持分段处理、总结、润色、纠错等功能",
            model_type=model_type,
            config=default_config
        )
    
    async def process(self, text: str, action: str, system_prompt: str = None, user_prompt: str = None, **kwargs) -> str:
        """处理长文本
        
        Args:
            text: 要处理的文本
            action: 操作类型（summarize, polish, correct, extract_keywords, structure）
            system_prompt: 系统设定提示词
            user_prompt: 用户设定提示词
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        try:
            if not text or len(text.strip()) == 0:
                return "输入文本为空，无法处理"
            
            # 将系统设定和用户设定传递给处理方法
            kwargs['system_prompt'] = system_prompt
            kwargs['user_prompt'] = user_prompt
            
            # 检查文本长度是否需要分段处理
            estimated_tokens = self._estimate_tokens(text)
            max_tokens = self.config.get("max_tokens_per_segment", 40000)
            
            if estimated_tokens <= max_tokens:
                # 文本较短，直接处理
                return await self._process_single_segment(text, action, **kwargs)
            else:
                # 文本较长，需要分段处理
                return await self._process_long_text(text, action, **kwargs)
                
        except Exception as e:
            return f"处理文本时出错: {str(e)}"
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: 估算的token数量
        """
        # 简单估算：中文字符按1.5个token计算，英文单词按1个token计算
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        other_chars = len(text) - chinese_chars - english_words
        
        estimated_tokens = int(chinese_chars * 1.5 + english_words + other_chars * 0.5)
        return max(estimated_tokens, len(text) // 4)  # 最少按4字符1token计算
    
    def _split_text_into_segments(self, text: str) -> List[str]:
        """将长文本分割成多个段落
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分割后的段落列表
        """
        max_tokens = self.config.get("max_tokens_per_segment", 40000)
        overlap_tokens = self.config.get("overlap_tokens", 200)
        min_length = self.config.get("min_segment_length", 100)
        
        # 首先按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        segments = []
        current_segment = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 检查当前段落加入后是否超过限制
            test_segment = current_segment + "\n\n" + paragraph if current_segment else paragraph
            
            if self._estimate_tokens(test_segment) <= max_tokens:
                current_segment = test_segment
            else:
                # 当前段落会导致超限
                if current_segment and len(current_segment) >= min_length:
                    segments.append(current_segment)
                    
                    # 添加重叠内容以保持上下文
                    if overlap_tokens > 0:
                        overlap_text = self._get_text_tail(current_segment, overlap_tokens)
                        current_segment = overlap_text + "\n\n" + paragraph
                    else:
                        current_segment = paragraph
                else:
                    current_segment = test_segment
                
                # 如果单个段落就超过限制，需要进一步分割
                if self._estimate_tokens(current_segment) > max_tokens:
                    sub_segments = self._split_large_paragraph(current_segment, max_tokens, overlap_tokens)
                    segments.extend(sub_segments[:-1])
                    current_segment = sub_segments[-1] if sub_segments else ""
        
        # 添加最后一个段落
        if current_segment and len(current_segment) >= min_length:
            segments.append(current_segment)
        
        return segments
    
    def _split_large_paragraph(self, paragraph: str, max_tokens: int, overlap_tokens: int) -> List[str]:
        """分割过大的段落
        
        Args:
            paragraph: 要分割的段落
            max_tokens: 最大token数
            overlap_tokens: 重叠token数
            
        Returns:
            List[str]: 分割后的子段落列表
        """
        # 按句子分割
        sentences = re.split(r'[。！？.!?]', paragraph)
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 恢复标点符号（简单处理）
            if not sentence.endswith(('。', '！', '？', '.', '!', '?')):
                sentence += '。'
                
            test_segment = current_segment + sentence if current_segment else sentence
            
            if self._estimate_tokens(test_segment) <= max_tokens:
                current_segment = test_segment
            else:
                if current_segment:
                    segments.append(current_segment)
                    
                    # 添加重叠内容
                    if overlap_tokens > 0:
                        overlap_text = self._get_text_tail(current_segment, overlap_tokens)
                        current_segment = overlap_text + sentence
                    else:
                        current_segment = sentence
                else:
                    # 单个句子就超过限制，强制分割
                    current_segment = sentence
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _get_text_tail(self, text: str, max_tokens: int) -> str:
        """获取文本的尾部内容作为重叠部分
        
        Args:
            text: 输入文本
            max_tokens: 最大token数
            
        Returns:
            str: 尾部文本
        """
        if self._estimate_tokens(text) <= max_tokens:
            return text
        
        # 简单处理：取后面的字符
        estimated_chars = max_tokens * 2  # 粗略估算
        return text[-estimated_chars:] if len(text) > estimated_chars else text
    
    async def _process_single_segment(self, text: str, action: str, **kwargs) -> str:
        """处理单个文本段落
        
        Args:
            text: 文本段落
            action: 操作类型
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        try:
            # 提取系统设定和用户设定
            system_prompt = kwargs.pop('system_prompt', None)
            user_prompt = kwargs.pop('user_prompt', None)
            
            result = await self.call_api(text, action, system_prompt=system_prompt, user_prompt=user_prompt, **kwargs)
            return result
        except Exception as e:
            return f"处理单个段落时出错: {str(e)}"
    
    async def _process_long_text(self, text: str, action: str, **kwargs) -> str:
        """处理长文本
        
        Args:
            text: 长文本
            action: 操作类型
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        # 分割文本
        segments = self._split_text_into_segments(text)
        
        if not segments:
            return "文本分割失败，无法处理"
        
        print(f"[长文本处理] 文本已分割为 {len(segments)} 个段落")
        
        # 处理每个段落
        processed_segments = []
        context_summary = ""  # 用于保持上下文连贯性
        
        for i, segment in enumerate(segments):
            print(f"[长文本处理] 正在处理第 {i+1}/{len(segments)} 个段落...")
            
            # 构建带上下文的prompt
            if self.config.get("preserve_context", True) and context_summary and action in ["summarize", "structure"]:
                context_prompt = f"前文概要：{context_summary}\n\n当前段落：{segment}"
                processed_segment = await self._process_single_segment(context_prompt, action, **kwargs)
            else:
                processed_segment = await self._process_single_segment(segment, action, **kwargs)
            
            processed_segments.append(processed_segment)
            
            # 更新上下文概要（仅对总结类操作）
            if action == "summarize" and len(processed_segment) < len(segment):
                context_summary = processed_segment[:200] + "..." if len(processed_segment) > 200 else processed_segment
        
        # 合并处理结果
        return await self._merge_processed_segments(processed_segments, action, **kwargs)
    
    async def _merge_processed_segments(self, segments: List[str], action: str, **kwargs) -> str:
        """合并处理后的段落
        
        Args:
            segments: 处理后的段落列表
            action: 操作类型
            **kwargs: 额外参数
            
        Returns:
            str: 合并后的文本
        """
        if not segments:
            return ""
        
        if action == "summarize":
            # 对于总结，需要进一步整合
            combined_summary = "\n\n".join(segments)
            
            # 如果合并后的总结仍然很长，进行二次总结
            if self._estimate_tokens(combined_summary) > self.config.get("max_tokens_per_segment", 40000):
                final_summary_prompt = f"请将以下分段总结整合为一个完整、连贯的总结：\n\n{combined_summary}"
                return await self._process_single_segment(final_summary_prompt, "summarize", **kwargs)
            else:
                return combined_summary
        
        elif action == "structure":
            # 对于结构化整理，添加章节标题
            structured_text = ""
            for i, segment in enumerate(segments, 1):
                structured_text += f"## 第{i}部分\n\n{segment}\n\n"
            return structured_text.strip()
        
        elif action == "extract_keywords":
            # 对于关键词提取，去重并合并
            all_keywords = []
            for segment in segments:
                keywords = [kw.strip() for kw in segment.split(',') if kw.strip()]
                all_keywords.extend(keywords)
            
            # 去重并保持顺序
            unique_keywords = []
            seen = set()
            for kw in all_keywords:
                if kw.lower() not in seen:
                    unique_keywords.append(kw)
                    seen.add(kw.lower())
            
            return ", ".join(unique_keywords)
        
        else:
            # 对于润色、纠错等，直接连接
            return "\n\n".join(segments)
    
    def get_processing_options(self) -> Dict[str, str]:
        """获取支持的处理选项
        
        Returns:
            Dict[str, str]: 处理选项字典，键为选项代码，值为选项描述
        """
        return {
            "summarize": "总结 - 提取文本关键信息，生成简洁摘要",
            "polish": "润色 - 优化语言表达，提升可读性和流畅性",
            "correct": "纠错 - 检测并修正拼写、语法、逻辑错误",
            "extract_keywords": "关键词提取 - 提取文本中的核心关键词",
            "structure": "结构化整理 - 按主题或逻辑关系整理文本结构",
            "translate": "翻译 - 将文本翻译为指定语言"
        }
    
    def estimate_processing_time(self, text: str, action: str) -> int:
        """估算处理时间（秒）
        
        Args:
            text: 输入文本
            action: 操作类型
            
        Returns:
            int: 估算的处理时间（秒）
        """
        estimated_tokens = self._estimate_tokens(text)
        max_tokens = self.config.get("max_tokens_per_segment", 40000)
        
        # 计算需要的段落数
        segments_count = math.ceil(estimated_tokens / max_tokens)
        
        # 每个段落的基础处理时间（秒）
        base_time_per_segment = {
            "summarize": 15,
            "polish": 10,
            "correct": 8,
            "extract_keywords": 5,
            "structure": 12,
            "translate": 20
        }.get(action, 10)
        
        total_time = segments_count * base_time_per_segment
        
        # 如果需要二次处理（如总结的整合），增加额外时间
        if action == "summarize" and segments_count > 1:
            total_time += 10
        
        return max(total_time, 5)  # 最少5秒