import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_file = "chat_ui_config.json"
        self.default_config = {
            "chat_ui": {
                "api_url": "https://api.deepseek.com/v1/chat/completions",
                "api_key": "",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "host": "0.0.0.0",
                "port": 5001,
                "max_file_size": 32 * 1024 * 1024,  # 32MB
                "log_level": "INFO",
                "enable_history": True,
                "max_history": 100,
                "enable_file_upload": True,
                "allowed_extensions": [".txt", ".pdf", ".doc", ".docx", ".md"],
                "upload_dir": "uploads",
                "temp_dir": "temp"
            }
        }
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置和已存在的配置
                    return self.merge_config(self.default_config, config)
            else:
                # 如果配置文件不存在，创建默认配置
                self.save_config(self.default_config)
                return self.default_config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return self.default_config

    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def merge_config(self, default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和当前配置"""
        merged = default.copy()
        for key, value in current.items():
            if key in merged:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = self.merge_config(merged[key], value)
                else:
                    merged[key] = value
            else:
                merged[key] = value
        return merged

    def get_config(self, section: str = None) -> Dict[str, Any]:
        """获取配置，可以指定section"""
        if section:
            return self.config.get(section, {})
        return self.config

    def update_config(self, section: str, key: str, value: Any) -> None:
        """更新配置"""
        if section in self.config:
            self.config[section][key] = value
            self.save_config(self.config)

    def get_api_url(self) -> str:
        """获取API URL"""
        return self.config["chat_ui"]["api_url"]

    def get_api_key(self) -> str:
        """获取API Key"""
        return self.config["chat_ui"]["api_key"]

    def get_model(self) -> str:
        """获取模型名称"""
        return self.config["chat_ui"]["model"]

    def get_temperature(self) -> float:
        """获取温度参数"""
        return self.config["chat_ui"]["temperature"]

    def get_host(self) -> str:
        """获取主机地址"""
        return self.config["chat_ui"]["host"]

    def get_port(self) -> int:
        """获取端口号"""
        return self.config["chat_ui"]["port"]

    def get_max_file_size(self) -> int:
        """获取最大文件大小"""
        return self.config["chat_ui"]["max_file_size"]

    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.config["chat_ui"]["log_level"]

    def is_history_enabled(self) -> bool:
        """是否启用历史记录"""
        return self.config["chat_ui"]["enable_history"]

    def get_max_history(self) -> int:
        """获取最大历史记录数"""
        return self.config["chat_ui"]["max_history"]

    def is_file_upload_enabled(self) -> bool:
        """是否启用文件上传"""
        return self.config["chat_ui"]["enable_file_upload"]

    def get_allowed_extensions(self) -> list:
        """获取允许的文件扩展名"""
        return self.config["chat_ui"]["allowed_extensions"]

    def get_upload_dir(self) -> str:
        """获取上传目录"""
        return self.config["chat_ui"]["upload_dir"]

    def get_temp_dir(self) -> str:
        """获取临时目录"""
        return self.config["chat_ui"]["temp_dir"]

# 创建全局配置管理器实例
config_manager = ConfigManager()

# 导出配置和更新函数
config = config_manager.get_config()
update_config = config_manager.update_config 