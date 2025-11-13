import json
import os
from typing import Dict, Any
from pathlib import Path

class PromptConfigManager:
    def __init__(self):
        self.config_file = "prompt_config.json"
        self.default_config = {
            "system_prompts": {
                "总结": "你是一个专业的文本总结助手。你的任务是提取文本的关键信息，生成简洁明了的摘要。请保持客观性，突出重点内容。",
                "润色": "你是一个专业的文本润色助手。你的任务是修正语音输入中的错误，包括错别字、语法错误和标点符号问题，同时保持原文的意思和风格。",
                "纠错": "你是一个专业的文本纠错助手。你的任务是检测并修正文本中的拼写、语法和逻辑错误，确保文本的准确性和可读性。",
                "关键词提取": "你是一个专业的关键词提取助手。你的任务是从文本中提取最重要的关键词和短语，帮助用户快速了解文本核心内容。",
                "结构化整理": "你是一个专业的文本结构化助手。你的任务是将文本按照逻辑关系进行整理和结构化，使内容更加清晰易读。",
                "纠正错误和划分段落，不总结": "你是一个专业的文本编辑助手。你的任务是纠正文本中的错误并合理划分段落，但不要总结或改变原文内容。"
            },
            "user_prompts": {
                "总结": "请总结以下文本的要点，提取关键信息，生成简洁的摘要：",
                "润色": "请润色以下文本，修正语音输入中的错误，补充标点符号，保持原意不变：",
                "纠错": "请纠正以下文本中的拼写、语法和逻辑错误：",
                "关键词提取": "请从以下文本中提取最重要的关键词和短语：",
                "结构化整理": "请将以下文本进行结构化整理，按逻辑关系组织内容：",
                "纠正错误和划分段落，不总结": "请纠正以下文本中的错误并合理划分段落，保持原文内容不变："
            },
            "current_prompts": {
                "system_prompt": "",
                "user_prompt": ""
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
            print(f"加载提示词配置文件失败: {e}")
            return self.default_config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """保存配置到文件"""
        try:
            config_to_save = config if config is not None else self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存提示词配置文件失败: {e}")

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

    def get_system_prompt(self, process_type: str) -> str:
        """获取指定处理类型的系统提示词"""
        return self.config.get("system_prompts", {}).get(process_type, "你是一个专业的文本处理助手。")

    def get_user_prompt(self, process_type: str) -> str:
        """获取指定处理类型的用户提示词"""
        return self.config.get("user_prompts", {}).get(process_type, f"请{process_type}以下文本：")

    def save_current_prompts(self, system_prompt: str, user_prompt: str) -> None:
        """保存当前的提示词设置"""
        self.config["current_prompts"]["system_prompt"] = system_prompt
        self.config["current_prompts"]["user_prompt"] = user_prompt
        self.save_config()

    def get_current_prompts(self) -> Dict[str, str]:
        """获取当前保存的提示词设置"""
        return self.config.get("current_prompts", {"system_prompt": "", "user_prompt": ""})

    def update_system_prompt(self, process_type: str, prompt: str) -> None:
        """更新指定处理类型的系统提示词"""
        if "system_prompts" not in self.config:
            self.config["system_prompts"] = {}
        self.config["system_prompts"][process_type] = prompt
        self.save_config()

    def update_user_prompt(self, process_type: str, prompt: str) -> None:
        """更新指定处理类型的用户提示词"""
        if "user_prompts" not in self.config:
            self.config["user_prompts"] = {}
        self.config["user_prompts"][process_type] = prompt
        self.save_config()

# 创建全局实例
prompt_config_manager = PromptConfigManager()