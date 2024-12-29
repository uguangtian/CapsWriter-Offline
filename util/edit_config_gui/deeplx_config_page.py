from PySide6.QtCore import Qt
from siui.components import (
    SiLineEditWithDeletionButton,
    SiTitledWidgetGroup,
)
from siui.components.option_card import SiOptionCardLinear
from siui.components.page import SiPage
from siui.components.spinbox.spinbox import SiIntSpinBox
from siui.core import SiGlobal

from .select_path import SelectPath
from .set_default_button import SetDefaultButton


class DeeplxConfigPage(SiPage):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.deeplx_exe_path: str = ""
        self.init_ui()
        self.online_translate_port_set_default.clicked.connect(
            lambda: self.online_translate_port.setValue(1188)
        )
        self.api_set_default.clicked.connect(
            lambda: self.api.lineEdit().setText("http://127.0.0.1:1188/translate")
        )

    def init_ui(self):
        self.setPadding(64)
        self.setScrollMaximumWidth(1000)
        self.setScrollAlignment(Qt.AlignLeft)
        self.setTitle("DeepLX 配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        with self.titled_widgets_group as group:
            group.addTitle("通用")

            # DeepLX 可执行文件路径
            self.deeplx_exe_path_selector = SelectPath(
                self,
                title="DeepLX 可执行文件位置",
                label_text="用于在线翻译",
                default_path=self.config["deeplx"]["exe_path"],
                file_filter="Executables (*.exe)",
                mode="file",
                on_path_selected=self.on_deeplx_exe_path_selected,
            )
            group.addWidget(self.deeplx_exe_path_selector)

            # DeepLX 在线翻译服务端口
            self.online_translate_port = SiIntSpinBox(group)
            self.online_translate_port.resize(256, 32)
            self.online_translate_port.setMinimum(1024)
            self.online_translate_port.setMaximum(65535)
            self.online_translate_port.setValue(
                int(self.config["deeplx"]["online_translate_port"])
            )
            self.online_translate_port_set_default = SetDefaultButton(self)
            self.online_translate_port_linear_attaching = SiOptionCardLinear(self)
            self.online_translate_port_linear_attaching.setTitle(
                "DeepLX 在线翻译服务端口", '默认值："1188" 端口号范围 1024-65535'
            )
            self.online_translate_port_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.online_translate_port_linear_attaching.addWidget(
                self.online_translate_port_set_default
            )
            self.online_translate_port_linear_attaching.addWidget(
                self.online_translate_port
            )
            group.addWidget(self.online_translate_port_linear_attaching)

            # DeepLX API 地址
            self.api = SiLineEditWithDeletionButton(self)
            self.api.lineEdit().setText(self.config["deeplx"]["api"])
            self.api.resize(256, 32)
            self.api_set_default = SetDefaultButton(self)
            self.api_linear_attaching = SiOptionCardLinear(self)
            self.api_linear_attaching.setTitle(
                "DeepLX API 地址", '默认值："http://127.0.0.1:1188/translate"'
            )
            self.api_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.api_linear_attaching.addWidget(self.api_set_default)
            self.api_linear_attaching.addWidget(self.api)
            group.addWidget(self.api_linear_attaching)

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)

    def on_deeplx_exe_path_selected(self, path):
        self.deeplx_exe_path = path
        print(f"Deeplx exe path selected: {self.deeplx_exe_path}")
