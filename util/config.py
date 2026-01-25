from pathlib import Path
from tomlkit import parse
import sys
import os

# 加载TOML配置文件
# 在打包后的应用中，使用 sys._MEIPASS 获取资源路径
if getattr(sys, 'frozen', False):
    # 打包后的环境
    base_path = Path(sys._MEIPASS)
else:
    # 开发环境
    base_path = Path(__file__).parent.parent

config_toml_path = base_path / "config.toml"
with config_toml_path.open("r", encoding="utf-8") as f:
    config_str = f.read()
    config = parse(config_str)


# 服务端配置
class ServerConfig:
    model: str = config.get("server").get("model")
    addr: str = config.get("server").get("addr")
    speech_recognition_port: int = config.get("server").get("speech_recognition_port")
    start_online_translate_server: bool = config.get("server").get("start_online_translate_server")
    start_offline_translate_server: bool = config.get("server").get("start_offline_translate_server")
    offline_translate_port: str = config.get("server").get("offline_translate_port")
    format_num: bool = config.get("server").get("format_num")
    format_punc: bool = config.get("server").get("format_punc")
    format_spell: bool = config.get("server").get("format_spell")
    shrink_automatically_to_tray: bool = config.get("server").get("shrink_automatically_to_tray")
    only_run_once: bool = config.get("server").get("only_run_once")
    in_the_meantime_start_the_client: bool = config.get("server").get("in_the_meantime_start_the_client")
    in_the_meantime_start_the_client_and_run_as_admin: bool = config.get("server").get("in_the_meantime_start_the_client_and_run_as_admin")

class LMStudioConfig:
    start_lmstudio_server: bool = config.get("lmstudio").get("start_lmstudio_server")
    lmstudio_port: int = config.get("lmstudio").get("lmstudio_port")
    lmstudio_api: str = config.get("lmstudio").get("lmstudio_api")
    lmstudio_model: str = config.get("lmstudio").get("lmstudio_model")
    temperature: float = config.get("lmstudio").get("temperature")
    max_tokens: int = config.get("lmstudio").get("max_tokens")
    api_endpoint: str = config.get("lmstudio").get("api_endpoint")

# 客户端配置
class ClientConfig:
    addr: str = config.get("client").get("addr")
    speech_recognition_port: str = config.get("client").get("speech_recognition_port")
    offline_translate_port: str = config.get("client").get("offline_translate_port")
    offline_translate_port_gemma2b: str = config.get("client").get("offline_translate_port_gemma2b")
    speech_recognition_shortcut: str = config.get("client").get("speech_recognition_shortcut")
    use_offline_translate_function: bool = config.get("client").get("use_offline_translate_function")
    offline_translate_shortcut: str = config.get("client").get("offline_translate_shortcut")
    offline_translate_and_replace_the_selected_text_shortcut: str = config.get("client").get("offline_translate_and_replace_the_selected_text_shortcut")
    use_online_translate_function: bool = config.get("client").get("use_online_translate_function")
    online_translate_shortcut: str = config.get("client").get("online_translate_shortcut")
    online_translate_target_languages: str = config.get("client").get("online_translate_target_languages")
    online_translate_and_replace_the_selected_text_shortcut: str = config.get("client").get("online_translate_and_replace_the_selected_text_shortcut")
    use_search_selected_text_with_everything_function: bool = config.get("client").get("use_search_selected_text_with_everything_function")
    search_selected_text_with_everything_shortcut: str = config.get("client").get("search_selected_text_with_everything_shortcut")
    everything_exe_path: str = config.get("client").get("everything_exe_path")
    hold_mode: bool = config.get("client").get("hold_mode")
    suppress: bool = config.get("client").get("suppress")
    restore_key: bool = config.get("client").get("restore_key")
    threshold: float = config.get("client").get("threshold")
    paste: bool = config.get("client").get("paste")
    restore_clipboard_after_paste: bool = config.get("client").get("restore_clipboard_after_paste")
    save_audio: bool = config.get("client").get("save_audio")
    save_markdown: bool = config.get("client").get("save_markdown")
    audio_name_len: int = config.get("client").get("audio_name_len")
    reduce_audio_files: bool = config.get("client").get("reduce_audio_files")
    trash_punc: str = config.get("client").get("trash_punc")
    hot_zh: bool = config.get("client").get("hot_zh")
    多音字: bool = config.get("client").get("多音字")
    声调: bool = config.get("client").get("声调")
    hot_en: bool = config.get("client").get("hot_en")
    hot_rule: bool = config.get("client").get("hot_rule")
    hot_kwd: bool = config.get("client").get("hot_kwd")
    mic_seg_duration: int = config.get("client").get("mic_seg_duration")
    mic_seg_overlap: int = config.get("client").get("mic_seg_overlap")
    file_seg_duration: int = config.get("client").get("file_seg_duration")
    file_seg_overlap: int = config.get("client").get("file_seg_overlap")
    mute_other_audio: bool = config.get("client").get("mute_other_audio")
    pause_other_audio: bool = config.get("client").get("pause_other_audio")
    arabic_year_number: bool = config.get("client").get("arabic_year_number")
    shrink_automatically_to_tray: bool = config.get("client").get("shrink_automatically_to_tray")
    only_run_once: bool = config.get("client").get("only_run_once")
    only_enable_microphones_when_pressed_record_shortcut: bool = config.get("client").get("only_enable_microphones_when_pressed_record_shortcut")
    microphone_device_index: int = config.get("client").get("microphone_device_index")
    microphone_device_name: str = config.get("client").get("microphone_device_name",{})
    vscode_exe_path: str = config.get("client").get("vscode_exe_path")
    play_start_music: bool = config.get("client").get("play_start_music")
    start_music_path: Path = Path(config.get("client").get("start_music_path"))
    start_music_volume: str = config.get("client").get("start_music_volume")
    play_stop_music: bool = config.get("client").get("play_stop_music")
    stop_music_path: Path = Path(config.get("client").get("stop_music_path"))
    stop_music_volume: str = config.get("client").get("stop_music_volume")
    hint_while_recording_at_edit_position_powered_by_ahk: bool = config.get("client").get("hint_while_recording_at_edit_position_powered_by_ahk")
    hint_while_recording_at_cursor_position: bool = config.get("client").get("hint_while_recording_at_cursor_position")
    check_microphone_usage_by: str = config.get("client").get("check_microphone_usage_by")
    enable_double_click_opposite_state: bool = config.get("client").get("enable_double_click_opposite_state")
    convert_to_traditional_chinese_main: str = config.get("client").get("convert_to_traditional_chinese_main")
    opencc_converter: str = config.get("client").get("opencc_converter")


# DeepLX 配置
class DeepLXConfig:
    online_translate_port: str = config.get("deeplx").get("online_translate_port")
    exe_path: Path = Path(config.get("deeplx").get("exe_path"))
    api: str = config.get("deeplx").get("api")


# DeepSeek 配置
class DeepSeekConfig:
    start_deepseek_server: bool = config.get("deepseek", {}).get("start_deepseek_server", False)
    deepseek_port: int = config.get("deepseek", {}).get("deepseek_port", "6018")
    api_key: str = config.get("deepseek", {}).get("api_key", "")
    api_endpoint: str = config.get("deepseek", {}).get("api_endpoint", "https://api.deepseek.com/v1/chat/completions")
    base_url: str = config.get("deepseek", {}).get("base_url", "https://api.deepseek.com/v1")
    model: str = config.get("deepseek", {}).get("model", "deepseek-chat")
    temperature: float = config.get("deepseek", {}).get("temperature", 0.7)
    max_tokens: int = config.get("deepseek", {}).get("max_tokens", 2000)


# 模型路径配置
class ModelPaths:
    model_dir: Path = Path(config.get("model_paths").get("model_dir"))
    sensevoice_path: Path = Path(config.get("model_paths").get("sensevoice_path"))
    sensevoice_tokens_path: Path = Path(config.get("model_paths").get("sensevoice_tokens_path"))
    paraformer_path: Path = Path(config.get("model_paths").get("paraformer_path"))
    paraformer_tokens_path: Path = Path(config.get("model_paths").get("paraformer_tokens_path"))
    punc_model_dir: Path = Path(config.get("model_paths").get("punc_model_dir"))
    opus_mt_dir: Path = Path(config.get("model_paths").get("opus_mt_dir"))
    funasr_nano_dir: Path = Path(config.get("model_paths").get("funasr_nano_dir"))


# SenseVoice 参数配置
class SenseVoiceArgs:
    model: str = config.get("model_paths").get("sensevoice_path")
    tokens: str = config.get("model_paths").get("sensevoice_tokens_path")
    num_threads: int = config.get("sensevoice_args").get("num_threads")
    sample_rate: int = config.get("sensevoice_args").get("sample_rate")
    feature_dim: int = config.get("sensevoice_args").get("feature_dim")
    decoding_method: str = config.get("sensevoice_args").get("decoding_method")
    debug: bool = config.get("sensevoice_args").get("debug")
    provider: str = config.get("sensevoice_args").get("provider")
    language: str = config.get("sensevoice_args").get("language")
    use_itn: bool = config.get("sensevoice_args").get("use_itn")
    rule_fsts: str = config.get("sensevoice_args").get("rule_fsts")
    rule_fars: str = config.get("sensevoice_args").get("rule_fars")


# Paraformer 参数配置
class ParaformerArgs:
    paraformer: str = config.get("model_paths").get("paraformer_path")
    tokens: str = config.get("model_paths").get("paraformer_tokens_path")
    num_threads: int = config.get("paraformer_args").get("num_threads")
    sample_rate: int = config.get("paraformer_args").get("sample_rate")
    feature_dim: int = config.get("paraformer_args").get("feature_dim")
    decoding_method: str = config.get("paraformer_args").get("decoding_method")
    debug: bool = config.get("paraformer_args").get("debug")


# FunASR-Nano 参数配置
class FunASRNanoArgs:
    encoder_adaptor: str = str(ModelPaths.funasr_nano_dir / "encoder_adaptor.int8.onnx")
    llm: str = str(ModelPaths.funasr_nano_dir / "llm_int8" / "llm.int8.onnx")
    embedding: str = str(ModelPaths.funasr_nano_dir / "embedding.int8.onnx")
    tokenizer: str = str(ModelPaths.funasr_nano_dir / "Qwen3-0.6B")
    num_threads: int = config.get("funasr_nano_args").get("num_threads")
    sample_rate: int = config.get("funasr_nano_args").get("sample_rate")
    feature_dim: int = config.get("funasr_nano_args").get("feature_dim")
    decoding_method: str = config.get("funasr_nano_args").get("decoding_method")
    debug: bool = config.get("funasr_nano_args").get("debug")
    provider: str = config.get("funasr_nano_args").get("provider")


# Claude 配置
class ClaudeConfig:
    start_claude_server: bool = config.get("claude", {}).get("start_claude_server", False)
    claude_port: int = config.get("claude", {}).get("claude_port", "6020")
    api_key: str = config.get("claude", {}).get("api_key", "")
    api_endpoint: str = config.get("claude", {}).get("api_endpoint", "")
    model: str = config.get("claude", {}).get("model", "")
    temperature: float = config.get("claude", {}).get("temperature", 0.7)
    max_tokens: int = config.get("claude", {}).get("max_tokens", 2000)

# 豆包配置（需要添加到现有配置文件中）
class DoubaoConfig:
    # 豆包API密钥
    api_key = "68f3d74d-7e12-4577-83e9-e64f787c28f0"
    
    # 豆包API端点
    api_endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    # 豆包模型
    # model = "doubao-1-5-pro-256k-250115"
    model = "doubao-1-5-lite-32k-250115"
    
    # 温度参数
    temperature = 0.7
    
    # 最大生成token数
    max_tokens = 1024
    
    # 豆包服务端口
    doubao_port = 6019


def print_config():
    """测试，打印所有配置信息"""

    def clearly_type(obj):
        import re

        result = type(obj).__name__
        match = re.search(r"'(.*?)'", result)
        if match:
            return match.group(1)
        else:
            return result

    from rich.console import Console
    from rich.table import Table

    console = Console()
    config_classes = [
        ServerConfig,
        ClientConfig,
        DeepLXConfig,
        ModelPaths,
        SenseVoiceArgs,
        ParaformerArgs,
        FunASRNanoArgs,
    ]

    for config_class in config_classes:
        table = Table(title=f"{config_class.__name__} 配置")

        table.add_column("属性名", style="cyan")
        table.add_column("类型", style="magenta")
        table.add_column("值", style="green")

        for key, value in config_class.__dict__.items():
            if not key.startswith("_"):
                attr_type = clearly_type(value)
                attr_value = str(value)
                table.add_row(key, attr_type, attr_value)

        console.print(table)


if __name__ == "__main__":
    print_config()
