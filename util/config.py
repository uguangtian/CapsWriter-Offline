from pathlib import Path
from tomlkit import parse

# 加载TOML配置文件
config_toml_path = Path(__file__).parent.parent / "config.toml"
with config_toml_path.open("r", encoding="utf-8") as f:
    config_str = f.read()
    config = parse(config_str)


# 服务端配置
class ServerConfig:
    model: str = config["server"]["model"]
    addr: str = config["server"]["addr"]
    speech_recognition_port: str = config["server"]["speech_recognition_port"]
    start_online_translate_server: bool = config["server"][
        "start_online_translate_server"
    ]
    start_offline_translate_server: bool = config["server"][
        "start_offline_translate_server"
    ]
    offline_translate_port: str = config["server"]["offline_translate_port"]
    format_num: bool = config["server"]["format_num"]
    format_punc: bool = config["server"]["format_punc"]
    format_spell: bool = config["server"]["format_spell"]
    shrink_automatically_to_tray: bool = config["server"][
        "shrink_automatically_to_tray"
    ]
    only_run_once: bool = config["server"]["only_run_once"]
    in_the_meantime_start_the_client: bool = config["server"][
        "in_the_meantime_start_the_client"
    ]
    in_the_meantime_start_the_client_and_run_as_admin: bool = config["server"][
        "in_the_meantime_start_the_client_and_run_as_admin"
    ]


# 客户端配置
class ClientConfig:
    addr: str = config["client"]["addr"]
    speech_recognition_port: str = config["client"]["speech_recognition_port"]
    offline_translate_port: str = config["client"]["offline_translate_port"]
    offline_translate_port_gemma2b: str = config["client"][
        "offline_translate_port_gemma2b"
    ]
    speech_recognition_shortcut: str = config["client"]["speech_recognition_shortcut"]
    use_offline_translate_function: bool = config["client"][
        "use_offline_translate_function"
    ]
    offline_translate_shortcut: str = config["client"]["offline_translate_shortcut"]
    offline_translate_and_replace_the_selected_text_shortcut: str = config["client"][
        "offline_translate_and_replace_the_selected_text_shortcut"
    ]
    use_online_translate_function: bool = config["client"][
        "use_online_translate_function"
    ]
    online_translate_shortcut: str = config["client"]["online_translate_shortcut"]
    online_translate_target_languages: str = config["client"][
        "online_translate_target_languages"
    ]
    online_translate_and_replace_the_selected_text_shortcut: str = config["client"][
        "online_translate_and_replace_the_selected_text_shortcut"
    ]
    use_search_selected_text_with_everything_function: bool = config["client"][
        "use_search_selected_text_with_everything_function"
    ]
    search_selected_text_with_everything_shortcut: str = config["client"][
        "search_selected_text_with_everything_shortcut"
    ]
    everything_exe_path: str = config["client"]["everything_exe_path"]
    hold_mode: bool = config["client"]["hold_mode"]
    suppress: bool = config["client"]["suppress"]
    restore_key: bool = config["client"]["restore_key"]
    threshold: float = config["client"]["threshold"]
    paste: bool = config["client"]["paste"]
    restore_clipboard_after_paste: bool = config["client"][
        "restore_clipboard_after_paste"
    ]
    save_audio: bool = config["client"]["save_audio"]
    save_markdown: bool = config["client"]["save_markdown"]
    audio_name_len: int = config["client"]["audio_name_len"]
    reduce_audio_files: bool = config["client"]["reduce_audio_files"]
    trash_punc: str = config["client"]["trash_punc"]
    hot_zh: bool = config["client"]["hot_zh"]
    多音字: bool = config["client"]["多音字"]
    声调: bool = config["client"]["声调"]
    hot_en: bool = config["client"]["hot_en"]
    hot_rule: bool = config["client"]["hot_rule"]
    hot_kwd: bool = config["client"]["hot_kwd"]
    mic_seg_duration: int = config["client"]["mic_seg_duration"]
    mic_seg_overlap: int = config["client"]["mic_seg_overlap"]
    file_seg_duration: int = config["client"]["file_seg_duration"]
    file_seg_overlap: int = config["client"]["file_seg_overlap"]
    mute_other_audio: bool = config["client"]["mute_other_audio"]
    pause_other_audio: bool = config["client"]["pause_other_audio"]
    arabic_year_number: bool = config["client"]["arabic_year_number"]
    shrink_automatically_to_tray: bool = config["client"][
        "shrink_automatically_to_tray"
    ]
    only_run_once: bool = config["client"]["only_run_once"]
    only_enable_microphones_when_pressed_record_shortcut: bool = config["client"][
        "only_enable_microphones_when_pressed_record_shortcut"
    ]
    vscode_exe_path: str = config["client"]["vscode_exe_path"]
    play_start_music: bool = config["client"]["play_start_music"]
    start_music_path: Path = Path(config["client"]["start_music_path"])
    start_music_volume: str = config["client"]["start_music_volume"]
    play_stop_music: bool = config["client"]["play_stop_music"]
    stop_music_path: Path = Path(config["client"]["stop_music_path"])
    stop_music_volume: str = config["client"]["stop_music_volume"]
    hint_while_recording_at_edit_position_powered_by_ahk: bool = config["client"][
        "hint_while_recording_at_edit_position_powered_by_ahk"
    ]
    hint_while_recording_at_cursor_position: bool = config["client"][
        "hint_while_recording_at_cursor_position"
    ]
    check_microphone_usage_by: str = config["client"]["check_microphone_usage_by"]
    enable_double_click_opposite_state: bool = config["client"][
        "enable_double_click_opposite_state"
    ]
    convert_to_traditional_chinese_main: str = config["client"][
        "convert_to_traditional_chinese_main"
    ]
    opencc_converter: str = config["client"]["opencc_converter"]


# DeepLX 配置
class DeepLXConfig:
    online_translate_port: str = config["deeplx"]["online_translate_port"]
    exe_path: Path = Path(config["deeplx"]["exe_path"])
    api: str = config["deeplx"]["api"]


# 模型路径配置
class ModelPaths:
    model_dir: Path = Path(config["model_paths"]["model_dir"])
    sensevoice_path: Path = Path(config["model_paths"]["sensevoice_path"])
    sensevoice_tokens_path: Path = Path(config["model_paths"]["sensevoice_tokens_path"])
    paraformer_path: Path = Path(config["model_paths"]["paraformer_path"])
    paraformer_tokens_path: Path = Path(config["model_paths"]["paraformer_tokens_path"])
    punc_model_dir: Path = Path(config["model_paths"]["punc_model_dir"])
    opus_mt_dir: Path = Path(config["model_paths"]["opus_mt_dir"])


# SenseVoice 参数配置
class SenseVoiceArgs:
    model: str = config["model_paths"]["sensevoice_path"]
    tokens: str = config["model_paths"]["sensevoice_tokens_path"]
    num_threads: int = config["sensevoice_args"]["num_threads"]
    sample_rate: int = config["sensevoice_args"]["sample_rate"]
    feature_dim: int = config["sensevoice_args"]["feature_dim"]
    decoding_method: str = config["sensevoice_args"]["decoding_method"]
    debug: bool = config["sensevoice_args"]["debug"]
    provider: str = config["sensevoice_args"]["provider"]
    language: str = config["sensevoice_args"]["language"]
    use_itn: bool = config["sensevoice_args"]["use_itn"]
    rule_fsts: str = config["sensevoice_args"]["rule_fsts"]
    rule_fars: str = config["sensevoice_args"]["rule_fars"]


# Paraformer 参数配置
class ParaformerArgs:
    paraformer: str = config["model_paths"]["paraformer_path"]
    tokens: str = config["model_paths"]["paraformer_tokens_path"]
    num_threads: int = config["paraformer_args"]["num_threads"]
    sample_rate: int = config["paraformer_args"]["sample_rate"]
    feature_dim: int = config["paraformer_args"]["feature_dim"]
    decoding_method: str = config["paraformer_args"]["decoding_method"]
    debug: bool = config["paraformer_args"]["debug"]


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
