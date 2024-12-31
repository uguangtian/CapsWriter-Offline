from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from siui.components import (
    SiDenseVContainer,
    SiTitledWidgetGroup,
)
from siui.components.button import (
    SiLongPressButtonRefactor,
)
from siui.components.page import SiPage
from siui.components.titled_widget_group import SiTitledWidgetGroup
from siui.components.widgets import (
    SiDenseVContainer,
)
from siui.core import SiGlobal

from .select_path import SelectPath


class ModelPathsConfigPage(SiPage):
    def __init__(self, config, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_path = config_path
        self.model_dir: str = self.config["model_paths"]["model_dir"]
        self.sensevoice_path: str = self.config["model_paths"]["sensevoice_path"]
        self.sensevoice_tokens_path: str = self.config["model_paths"][
            "sensevoice_tokens_path"
        ]
        self.paraformer_path: str = self.config["model_paths"]["paraformer_path"]
        self.paraformer_tokens_path: str = self.config["model_paths"][
            "paraformer_tokens_path"
        ]
        self.punc_model_dir: str = self.config["model_paths"]["punc_model_dir"]
        self.opus_mt_dir: str = self.config["model_paths"]["opus_mt_dir"]
        self.init_ui()
        self.model_dir_path_selector.pathSelected.connect(
            self.on_model_dir_path_selected
        )
        self.sensevoice_path_selector.pathSelected.connect(
            self.on_sensevoice_path_selected
        )
        self.sensevoice_tokens_path_selector.pathSelected.connect(
            self.on_sensevoice_tokens_path_selected
        )
        self.paraformer_path_selector.pathSelected.connect(
            self.on_paraformer_path_selected
        )
        self.paraformer_tokens_path_selector.pathSelected.connect(
            self.on_paraformer_tokens_path_selected
        )
        self.punc_model_dir_path_selector.pathSelected.connect(
            self.on_punc_model_dir_path_selected
        )
        self.opus_mt_dir_path_selector.pathSelected.connect(
            self.on_opus_mt_dir_path_selected
        )
        self.save.clicked.connect(self.save_config)

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
            )
            group.addWidget(self.opus_mt_dir_path_selector)

        with self.titled_widgets_group as group:
            # 保存配置
            self.save = SiLongPressButtonRefactor(self)
            self.save.setSvgIcon(SiGlobal.siui.iconpack.get("ic_fluent_save_filled"))
            self.save.setIconSize(QSize(32, 32))
            self.save.setText("\t保存 模型路径配置")
            self.save.setFont(QFont("Microsoft YaHei", 16))
            self.save.setToolTip("长按以确认")
            self.save.resize(420, 64)
            # 查看更多容器
            self.save_container = SiDenseVContainer(self)
            self.save_container.setAlignment(Qt.AlignCenter)
            self.save_container.addWidget(self.save)

            group.addWidget(self.save_container)

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

    def save_config(self):
        def get_value_from_gui():
            self.config["model_paths"]["model_dir"] = self.model_dir
            self.config["model_paths"]["sensevoice_path"] = self.sensevoice_path
            self.config["model_paths"]["sensevoice_tokens_path"] = (
                self.sensevoice_tokens_path
            )
            self.config["model_paths"]["paraformer_path"] = self.paraformer_path
            self.config["model_paths"]["paraformer_tokens_path"] = (
                self.paraformer_tokens_path
            )
            self.config["model_paths"]["punc_model_dir"] = self.punc_model_dir
            self.config["model_paths"]["opus_mt_dir"] = self.opus_mt_dir

        def print_config():
            from rich.console import Console
            from rich.table import Table

            from util.edit_config_gui.clearly_type import clearly_type

            console = Console()
            table = Table(title="保存 模型路径配置")
            table.add_column("属性名", style="cyan")
            table.add_column("类型", style="magenta")
            table.add_column("值", style="green")
            table.add_row(
                "model_dir",
                clearly_type(self.config["model_paths"]["model_dir"]),
                str(self.config["model_paths"]["model_dir"]),
            )
            table.add_row(
                "sensevoice_path",
                clearly_type(self.config["model_paths"]["sensevoice_path"]),
                str(self.config["model_paths"]["sensevoice_path"]),
            )
            table.add_row(
                "sensevoice_tokens_path",
                clearly_type(self.config["model_paths"]["sensevoice_tokens_path"]),
                str(self.config["model_paths"]["sensevoice_tokens_path"]),
            )
            table.add_row(
                "paraformer_path",
                clearly_type(self.config["model_paths"]["paraformer_path"]),
                str(self.config["model_paths"]["paraformer_path"]),
            )
            table.add_row(
                "paraformer_tokens_path",
                clearly_type(self.config["model_paths"]["paraformer_tokens_path"]),
                str(self.config["model_paths"]["paraformer_tokens_path"]),
            )
            table.add_row(
                "punc_model_dir",
                clearly_type(self.config["model_paths"]["punc_model_dir"]),
                str(self.config["model_paths"]["punc_model_dir"]),
            )
            table.add_row(
                "opus_mt_dir",
                clearly_type(self.config["model_paths"]["opus_mt_dir"]),
                str(self.config["model_paths"]["opus_mt_dir"]),
            )
            console.print(table)

        get_value_from_gui()
        print_config()
        from util.edit_config_gui.write_toml import write_toml

        write_toml(self.config, self.config_path)
