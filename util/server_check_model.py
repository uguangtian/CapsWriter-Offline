import sys
import os
import subprocess
from pathlib import Path

from util.config import ModelPaths, get_config_dict
from util.server_cosmic import console


def _normalize_paths():
    # SenseVoice: if model.int8.onnx not present but model.onnx exists, switch
    sv_path = Path(ModelPaths.sensevoice_path)
    if not sv_path.exists():
        alt = sv_path.parent / "model.onnx"
        if alt.exists():
            ModelPaths.sensevoice_path = alt


def _auto_download_models():
    # Set proxy for download script if needed
    os.environ["https_proxy"] = os.environ.get("https_proxy", "http://127.0.0.1:7890")
    os.environ["http_proxy"] = os.environ.get("http_proxy", "http://127.0.0.1:7890")
    
    try:
        from util.download_models_robust import main as download_main
        console.print("[yellow]正在尝试自动下载缺失的模型...")
        download_main()
    except Exception as e:
        console.print(f"[yellow]自动下载模型失败: {e}")


def _required_model_paths():
    """仅检查当前服务端配置实际会用到的模型路径。"""
    server = get_config_dict().get("server", {})
    model_name = str(server.get("model", "Paraformer")).lower()
    required: list[Path] = []
    if "sensevoice" in model_name:
        required.extend(
            [ModelPaths.sensevoice_path, ModelPaths.sensevoice_tokens_path]
        )
    else:
        required.extend(
            [ModelPaths.paraformer_path, ModelPaths.paraformer_tokens_path]
        )
    if server.get("format_punc", True):
        required.append(ModelPaths.punc_model_dir)
    if server.get("start_offline_translate_server", False):
        required.append(ModelPaths.opus_mt_dir)
    return required


def _all_models_exist():
    for path in _required_model_paths():
        p = Path(path)
        if not p.exists():
            return False, p
    return True, None


def check_model():
    _normalize_paths()
    ok, missing = _all_models_exist()
    if ok:
        return
    _auto_download_models()
    _normalize_paths()
    ok, missing = _all_models_exist()
    if ok:
        console.print("[green]模型文件已就绪")
        return
    console.print(
        f"""
    未能找到模型文件 

    未找到：{missing}

    本服务端需要 SenseVoice 模型、Paraformer语音模型、Helsinki-NLP--opus-mt-zh-en翻译模型
    请下载模型并放置到： {ModelPaths.model_dir} 
    
    Sensevoice语音模型：
    wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

    tar xvf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
    rm sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2



    Paraformer语音模型：
    git clone https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25 paraformer-offline-zh

    标点模型：
    git clone https://www.modelscope.cn/iic/punc_ct-transformer_cn-en-common-vocab471067-large-onnx.git punc_ct-transformer_cn-en


    翻译模型：
    https://huggingface.co/Helsinki-NLP/opus-mt-zh-en
    https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip

    将翻译模型文件解压放到软件根目录的 models/Helsinki-NLP--opus-mt-zh-en/ 文件夹中
""",
        style="bright_red",
    )
    input("按回车退出")
    sys.exit()


def check_model_gui():
    _normalize_paths()
    ok, missing = _all_models_exist()
    if ok:
        return
    _auto_download_models()
    _normalize_paths()
    ok, missing = _all_models_exist()
    if ok:
        return
    raise Exception(
        f"""
    未能找到模型文件 

    未找到：{missing}

    本服务端需要 SenseVoice 模型、Paraformer语音模型、Helsinki-NLP--opus-mt-zh-en翻译模型
    请下载模型并放置到： {ModelPaths.model_dir} 
    
    Sensevoice语音模型：
    wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

    tar xvf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
    rm sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2



    Paraformer语音模型：
    git clone https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25 paraformer-offline-zh

    标点模型：
    git clone https://www.modelscope.cn/iic/punc_ct-transformer_cn-en-common-vocab471067-large-onnx.git punc_ct-transformer_cn-en


    翻译模型：
    https://huggingface.co/Helsinki-NLP/opus-mt-zh-en
    https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip

    将翻译模型文件解压放到软件根目录的 models/Helsinki-NLP--opus-mt-zh-en/ 文件夹中
"""
    )
