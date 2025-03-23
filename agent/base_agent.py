# 基础Agent类

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union


class BaseAgent(ABC):
    """基础智能体类
    
    所有特定功能的智能体都应继承自此类，实现特定的处理逻辑。
    提供统一的接口进行文本处理，支持不同的大模型服务商。
    
    Attributes:
        name: 智能体名称
        description: 智能体描述
        model_type: 使用的模型类型
        config: 智能体配置
    """
    
    def __init__(self, 
                 name: str,
                 description: str,
                 model_type: str,
                 config: Dict[str, Any] = {}):
        """初始化基础智能体
        
        Args:
            name: 智能体名称
            description: 智能体描述
            model_type: 使用的模型类型，如'deepseek'、'doubao'或'lmstudio'
            config: 智能体配置参数
        """
        self.name = name
        self.description = description
        self.model_type = model_type.lower()
        self.config = config or {}
    
    @abstractmethod
    async def process(self, text: str, action: str, **kwargs) -> str:
        """处理文本的抽象方法，需要由子类实现
        
        Args:
            text: 要处理的文本
            action: 操作类型，如'polish'(润色)、'summarize'(总结)等
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        pass
    
    async def call_api(self, text: str, action: str, **kwargs) -> str:
        """调用对应模型的API处理文本
        
        根据model_type选择不同的API进行调用
        
        Args:
            text: 要处理的文本
            action: 操作类型
            **kwargs: 额外参数
            
        Returns:
            str: 处理后的文本
        """
        try:
            if self.model_type == 'deepseek':
                from model_services.deepseek_service import call_deepseek_api
                return await call_deepseek_api(text, action, **kwargs)
            elif self.model_type == 'doubao':
                from model_services.doubao_service import call_doubao_api
                return await call_doubao_api(text, action, **kwargs)
            elif self.model_type == 'lmstudio':
                from model_services.lmstudio_service import call_lmstudio_api
                return await call_lmstudio_api(text, action, **kwargs)
            elif self.model_type == 'claude':
                from model_services.claude_service import call_claude_api
                return await call_claude_api(text, action, **kwargs)
            else:
                raise ValueError(f"不支持的模型类型: {self.model_type}")
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            print(error_msg)
            return error_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """将智能体转换为字典格式
        
        Returns:
            Dict[str, Any]: 智能体的字典表示
        """
        return {
            "name": self.name,
            "description": self.description,
            "model_type": self.model_type,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseAgent':
        """从字典创建智能体实例
        
        Args:
            data: 智能体的字典表示
            
        Returns:
            BaseAgent: 智能体实例
        """
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            model_type=data.get("model_type", ""),
            config=data.get("config", {})
        )