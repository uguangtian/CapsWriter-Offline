#!/bin/bash

# 定义模型存放目录
MODELS_DIR="models"

# 创建模型目录（如果不存在）
if [ ! -d "$MODELS_DIR" ]; then
    mkdir -p "$MODELS_DIR"
fi

# 进入模型目录
cd "$MODELS_DIR"

# 下载 Sensevoice 语音模型
echo "正在下载 Sensevoice 语音模型..."
curl -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
echo "正在解压 Sensevoice 语音模型..."
tar xvf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
echo "正在删除 Sensevoice 语音模型压缩包..."
rm sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

# 下载 Paraformer 语音模型
echo "正在下载 Paraformer 语音模型..."
git clone https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25 paraformer-offline-zh

# 下载标点模型
echo "正在下载标点模型..."
git clone https://www.modelscope.cn/iic/punc_ct-transformer_cn-en-common-vocab471067-large-onnx.git punc_ct-transformer_cn-en

# 下载翻译模型
TRANSLATION_DIR="Helsinki-NLP--opus-mt-zh-en"
if [ ! -d "$TRANSLATION_DIR" ]; then
    mkdir -p "$TRANSLATION_DIR"
fi
echo "正在下载翻译模型（opus-2020-07-17.zip）..."
curl -O https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip
echo "正在解压翻译模型..."
unzip opus-2020-07-17.zip -d "$TRANSLATION_DIR"
echo "正在删除翻译模型压缩包..."
rm opus-2020-07-17.zip

echo "正在克隆 Helsinki-NLP/opus-mt-zh-en 仓库..."
git clone https://huggingface.co/Helsinki-NLP/opus-mt-zh-en "$TRANSLATION_DIR"

echo "所有模型下载和解压完成，已放置在 $MODELS_DIR 目录下。"
