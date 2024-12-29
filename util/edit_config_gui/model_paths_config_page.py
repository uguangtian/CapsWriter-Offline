from PySide6.QtCore import Qt
from siui.components import (
    SiTitledWidgetGroup,
)
from siui.components.page import SiPage

from .select_path import SelectPath


class ModelPathsConfigPage(SiPage):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.model_dir: str = ""
        self.sensevoice_path: str = ""
        self.sensevoice_tokens_path: str = ""
        self.paraformer_path: str = ""
        self.paraformer_tokens_path: str = ""
        self.punc_model_dir: str = ""
        self.opus_mt_dir: str = ""
        self.init_ui()

    def init_ui(self):
        self.setPadding(64)
        self.setScrollMaximumWidth(1000)
        self.setScrollAlignment(Qt.AlignLeft)
        self.setTitle("模型路径配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        with self.titled_widgets_group as group:
            group.addTitle("通用")

            # 模型文件目录
            self.model_dir_path_selector = SelectPath(
                self,
                title="模型文件总目录路径",
                label_text='默认值："models"\n本服务端需要 SenseVoice 模型、Paraformer语音模型、Helsinki-NLP--opus-mt-zh-en翻译模型\n请下载模型并放置到总目录对应的路径',
                default_path=self.config["model_paths"]["model_dir"],
                file_filter="",
                mode="directory",
                on_path_selected=self.on_model_dir_path_selected,
            )
            group.addWidget(self.model_dir_path_selector)

        with self.titled_widgets_group as group:
            group.addTitle("SenseVoice 语音模型")

            # SenseVoice 模型路径
            self.sensevoice_path_selector = SelectPath(
                self,
                title="SenseVoice 模型路径",
                label_text='默认值："models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/model.int8.onnx"',
                default_path=self.config["model_paths"]["sensevoice_path"],
                file_filter="*.onnx",
                mode="file",
                on_path_selected=self.on_sensevoice_path_selected,
            )
            group.addWidget(self.sensevoice_path_selector)

            # SenseVoice tokens 路径
            self.sensevoice_tokens_path_selector = SelectPath(
                self,
                title="SenseVoice tokens 路径",
                label_text='默认值："models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17/tokens.txt"',
                default_path=self.config["model_paths"]["sensevoice_tokens_path"],
                file_filter="*.txt",
                mode="file",
                on_path_selected=self.on_sensevoice_tokens_path_selected,
            )
            group.addWidget(self.sensevoice_tokens_path_selector)

        with self.titled_widgets_group as group:
            group.addTitle("Paraformer 语音模型")

            # Paraformer 模型路径
            self.paraformer_path_selector = SelectPath(
                self,
                title="Paraformer 模型路径",
                label_text='默认值："models/paraformer-offline-zh/model.int8.onnx"',
                default_path=self.config["model_paths"]["paraformer_path"],
                file_filter="*.onnx",
                mode="file",
                on_path_selected=self.on_paraformer_path_selected,
            )
            group.addWidget(self.paraformer_path_selector)

            # Paraformer tokens 路径
            self.paraformer_tokens_path_selector = SelectPath(
                self,
                title="Paraformer tokens 路径",
                label_text='默认值："models/paraformer-offline-zh/tokens.txt"',
                default_path=self.config["model_paths"]["paraformer_tokens_path"],
                file_filter="*.txt",
                mode="file",
                on_path_selected=self.on_paraformer_tokens_path_selected,
            )
            group.addWidget(self.paraformer_tokens_path_selector)

            # 标点模型目录
            self.punc_model_dir_path_selector = SelectPath(
                self,
                title="标点模型目录路径",
                label_text='默认值："models/punc_ct-transformer_cn-en"',
                default_path=self.config["model_paths"]["punc_model_dir"],
                file_filter="",
                mode="directory",
                on_path_selected=self.on_punc_model_dir_path_selected,
            )
            group.addWidget(self.punc_model_dir_path_selector)

        with self.titled_widgets_group as group:
            group.addTitle("Helsinki NLP--opus-mt-zh-en 离线翻译模型")

            # 离线翻译模型目录
            self.opus_mt_dir_path_selector = SelectPath(
                self,
                title="离线翻译模型目录路径",
                label_text='默认值："models/Helsinki-NLP--opus-mt-zh-en"',
                default_path=self.config["model_paths"]["opus_mt_dir"],
                file_filter="",
                mode="directory",
                on_path_selected=self.on_opus_mt_dir_path_selected,
            )
            group.addWidget(self.opus_mt_dir_path_selector)

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)

    def on_model_dir_path_selected(self, path: str):
        self.model_dir = path
        print(f"model_dir path selected: {self.model_dir}")

    def on_sensevoice_path_selected(self, path: str):
        self.sensevoice_path = path
        print(f"sensevoice_path selected: {self.sensevoice_path}")

    def on_sensevoice_tokens_path_selected(self, path: str):
        self.sensevoice_tokens_path = path
        print(f"sensevoice_tokens_path selected: {self.sensevoice_tokens_path}")

    def on_paraformer_path_selected(self, path: str):
        self.paraformer_path = path
        print(f"paraformer_path selected: {self.paraformer_path}")

    def on_paraformer_tokens_path_selected(self, path: str):
        self.paraformer_tokens_path = path
        print(f"paraformer_tokens_path selected: {self.paraformer_tokens_path}")

    def on_punc_model_dir_path_selected(self, path: str):
        self.punc_model_dir = path
        print(f"punc_model_dir selected: {self.punc_model_dir}")

    def on_opus_mt_dir_path_selected(self, path: str):
        self.opus_mt_dir = path
        print(f"opus_mt_dir selected: {self.opus_mt_dir}")
