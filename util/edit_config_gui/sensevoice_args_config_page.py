from PySide6.QtCore import Qt
from siui.components import (
    SiTitledWidgetGroup,
)
from siui.components.page import SiPage


class SenseVoiceArgsConfigPage(SiPage):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.setPadding(64)
        self.setScrollMaximumWidth(1000)
        self.setScrollAlignment(Qt.AlignLeft)
        self.setTitle("SenseVoice 语音识别模型参数配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        with self.titled_widgets_group as group:
            group.addTitle("通用")

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)
