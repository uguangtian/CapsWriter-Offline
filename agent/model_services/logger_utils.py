# 大模型服务日志工具模块

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ModelServiceLogger:
    """大模型服务专用日志记录器"""
    
    def __init__(self, service_name: str, log_level: str = "DEBUG"):
        """
        初始化日志记录器
        
        Args:
            service_name: 服务名称（如 'deepseek', 'claude' 等）
            log_level: 日志级别
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"model_service_{service_name}")
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 文件处理器 - 详细日志
        file_handler = logging.FileHandler(
            log_dir / f"model_service_{self.service_name}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器 - 简化日志
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        simple_formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_api_request(self, 
                       action: str, 
                       text_length: int, 
                       request_params: Dict[str, Any],
                       request_id: Optional[str] = None) -> str:
        """
        记录API请求日志
        
        Args:
            action: 操作类型
            text_length: 文本长度
            request_params: 请求参数
            request_id: 请求ID（如果没有提供会自动生成）
        
        Returns:
            str: 请求ID
        """
        if not request_id:
            request_id = f"{self.service_name}_{int(time.time() * 1000)}"
        
        # 过滤敏感信息
        safe_params = self._filter_sensitive_data(request_params)
        
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "text_length": text_length,
            "request_params": safe_params
        }
        
        self.logger.info(f"API请求开始 - ID: {request_id}, Action: {action}, 文本长度: {text_length}")
        self.logger.debug(f"请求详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
        
        return request_id
    
    def log_api_response(self, 
                        request_id: str, 
                        success: bool, 
                        response_data: Optional[Dict[str, Any]] = None,
                        error_message: Optional[str] = None,
                        response_length: Optional[int] = None,
                        duration_ms: Optional[float] = None):
        """
        记录API响应日志
        
        Args:
            request_id: 请求ID
            success: 是否成功
            response_data: 响应数据
            error_message: 错误信息
            response_length: 响应文本长度
            duration_ms: 请求耗时（毫秒）
        """
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_ms": duration_ms
        }
        
        if success:
            log_data["response_length"] = response_length
            if response_data:
                # 过滤敏感信息
                safe_response = self._filter_sensitive_data(response_data)
                log_data["response_data"] = safe_response
            
            self.logger.info(f"API请求成功 - ID: {request_id}, 响应长度: {response_length}, 耗时: {duration_ms:.2f}ms")
        else:
            log_data["error_message"] = error_message
            self.logger.error(f"API请求失败 - ID: {request_id}, 错误: {error_message}, 耗时: {duration_ms:.2f}ms")
        
        self.logger.debug(f"响应详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
    
    def log_websocket_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        记录WebSocket事件日志
        
        Args:
            event_type: 事件类型（如 'connection_established', 'connection_closed', 'message_received'）
            data: 事件数据
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "service": self.service_name
        }
        
        if data:
            safe_data = self._filter_sensitive_data(data)
            log_data["data"] = safe_data
        
        self.logger.info(f"WebSocket事件: {event_type}")
        self.logger.debug(f"事件详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤敏感数据
        
        Args:
            data: 原始数据
        
        Returns:
            Dict[str, Any]: 过滤后的安全数据
        """
        if not isinstance(data, dict):
            return data
        
        safe_data = data.copy()
        sensitive_keys = ['api_key', 'authorization', 'password', 'token', 'secret']
        
        for key in safe_data:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(safe_data[key], str) and len(safe_data[key]) > 8:
                    # 只显示前4位和后4位
                    safe_data[key] = f"{safe_data[key][:4]}****{safe_data[key][-4:]}"
                else:
                    safe_data[key] = "****"
            elif key.lower() == 'messages' and isinstance(safe_data[key], list):
                # 对于消息内容，只记录长度和前100个字符
                safe_messages = []
                for msg in safe_data[key]:
                    if isinstance(msg, dict) and 'content' in msg:
                        content = msg['content']
                        safe_msg = msg.copy()
                        if len(content) > 100:
                            safe_msg['content'] = f"{content[:100]}...(总长度:{len(content)})"
                        safe_messages.append(safe_msg)
                    else:
                        safe_messages.append(msg)
                safe_data[key] = safe_messages
        
        return safe_data
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)


# 创建各服务的日志记录器实例
deepseek_logger = ModelServiceLogger("deepseek")
doubao_logger = ModelServiceLogger("doubao")
claude_logger = ModelServiceLogger("claude")
lmstudio_logger = ModelServiceLogger("lmstudio")