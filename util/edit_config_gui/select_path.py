from PySide6.QtWidgets import QFileDialog
from siui.components import (
    SiLabel,
    SiLineEditWithDeletionButton,
    SiOptionCardPlane,
)
from siui.components.button import (
    SiPushButtonRefactor,
)
from siui.core import Si, SiGlobal


class SelectPath(SiOptionCardPlane):
    def __init__(
        self,
        parent,
        title,
        label_text,
        default_path,
        file_filter="",
        mode="file",
        on_path_selected=None,
    ):
        super().__init__(parent)
        self.setTitle(title)
        self.label_text = label_text
        self.default_path = default_path
        self.file_filter = file_filter
        self.mode = mode
        self.on_path_selected = on_path_selected

        # Create and add label
        self.label = SiLabel(self)
        self.label.setText(label_text)
        self.label.setSiliconWidgetFlag(Si.AdjustSizeOnTextChanged)
        self.label.setStyleSheet("color: {}".format(SiGlobal.siui.colors["TEXT_C"]))
        self.label.adjustSize()
        self.body().addWidget(self.label)

        # Create and configure path input
        self.path_input = SiLineEditWithDeletionButton(self)
        self.path_input.lineEdit().setText(default_path)
        self.path_input.resize(800, 32)

        # Create and configure selection button
        self.select_button = SiPushButtonRefactor(self)
        self.select_button.setSvgIcon(
            SiGlobal.siui.iconpack.get("ic_fluent_search_regular")
        )
        self.select_button.setToolTip("选择路径")
        self.select_button.adjustSize()
        self.select_button.clicked.connect(self.select_path)
        self.footer().addWidget(self.select_button, side="right")

        # Add path input to footer
        self.footer().addWidget(self.path_input, side="right")

        self.adjustSize()

    def select_path(self):
        if self.mode == "file":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", self.file_filter
            )
            if file_path:
                self.path_input.lineEdit().setText(file_path)
                if self.on_path_selected:
                    self.on_path_selected(file_path)
        elif self.mode == "directory":
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择目录", self.default_path
            )
            if dir_path:
                self.path_input.lineEdit().setText(dir_path)
                if self.on_path_selected:
                    self.on_path_selected(dir_path)
        else:
            raise ValueError("模式参数必须是 'file' 或 'directory'")
