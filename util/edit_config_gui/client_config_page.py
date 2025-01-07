from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from siui.components import (
    SiDenseVContainer,
    SiLineEditWithDeletionButton,
    SiTitledWidgetGroup,
)
from siui.components.button import (
    SiLongPressButtonRefactor,
    SiToggleButtonRefactor,
)
from siui.components.combobox import SiComboBox
from siui.components.option_card import SiOptionCardLinear
from siui.components.page import SiPage
from siui.components.slider_ import SiSlider
from siui.components.spinbox.spinbox import SiDoubleSpinBox, SiIntSpinBox
from siui.components.titled_widget_group import SiTitledWidgetGroup
from siui.components.widgets import (
    SiDenseVContainer,
    SiSwitch,
)
from siui.core import SiGlobal

from util.value_check import ValueCheck

from .select_path import SelectPath
from .set_default_button import SetDefaultButton


class ClientConfigPage(SiPage):
    def __init__(self, config, config_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.config_path = config_path
        self.vscode_exe_path: str = self.config["client"]["vscode_exe_path"]
        self.init_ui()
        self.vscode_exe_path_selector.pathSelected.connect(
            self.on_vscode_exe_path_selected
        )
        self.vscode_exe_path_selector.path_input.lineEdit().editingFinished.connect(
            lambda: self.on_vscode_exe_path_selected(
                self.vscode_exe_path_selector.path_input.lineEdit().text()
            )
        )
        self.addr_set_default.clicked.connect(
            lambda: self.addr.lineEdit().setText("127.0.0.1")
        )
        self.use_offline_translate_function.toggled.connect(
            lambda: self.use_offline_translate_function_changed()
        )
        self.speech_recognition_shortcut_set_default.clicked.connect(
            lambda: self.speech_recognition_shortcut.lineEdit().setText("caps lock")
        )
        self.speech_recognition_port_set_default.clicked.connect(
            lambda: self.speech_recognition_port.setValue(6016)
        )
        self.mic_seg_duration_set_default.clicked.connect(
            lambda: self.mic_seg_duration.setValue(15)
        )
        self.mic_seg_overlap_set_default.clicked.connect(
            lambda: self.mic_seg_overlap.setValue(2)
        )
        self.file_seg_duration_set_default.clicked.connect(
            lambda: self.file_seg_duration.setValue(25)
        )
        self.file_seg_overlap_set_default.clicked.connect(
            lambda: self.file_seg_overlap.setValue(2)
        )
        self.hold_mode.toggled.connect(lambda: self.hold_mode_changed())
        self.start_music_path_set_default.clicked.connect(
            lambda: self.start_music_path.lineEdit().setText("assets/start.mp3")
        )
        self.stop_music_path_set_default.clicked.connect(
            lambda: self.stop_music_path.lineEdit().setText("assets/stop.mp3")
        )
        self.hint_while_recording_at_cursor_position.toggled.connect(
            lambda: self.hint_while_recording_at_cursor_position_changed()
        )
        self.convert_to_traditional_chinese_main.toggled.connect(
            lambda: self.convert_to_traditional_chinese_main_changed()
        )
        self.offline_translate_port_set_default.clicked.connect(
            lambda: self.offline_translate_port.setValue(6017)
        )
        self.threshold_set_default.clicked.connect(lambda: self.threshold.setValue(0.3))
        self.offline_translate_shortcut_set_default.clicked.connect(
            lambda: self.offline_translate_shortcut.lineEdit().setText("left shift")
        )
        self.trash_punc_set_default.clicked.connect(
            lambda: self.trash_punc.lineEdit().setText("，。,.")
        )
        self.paste.toggled.connect(lambda: self.paste_changed())
        self.save_audio.toggled.connect(lambda: self.save_audio_changed())
        self.audio_name_len_set_default.clicked.connect(
            lambda: self.audio_name_len.setValue(20)
        )
        self.offline_translate_and_replace_the_selected_text_shortcut_set_default.clicked.connect(
            lambda: self.offline_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                "ctrl + alt + p"
            )
        )
        self.use_online_translate_function.toggled.connect(
            lambda: self.use_online_translate_function_changed()
        )
        self.online_translate_shortcut_set_default.clicked.connect(
            lambda: self.online_translate_shortcut.lineEdit().setText("right shift")
        )
        self.online_translate_target_languages_set_default.clicked.connect(
            lambda: self.online_translate_target_languages.menu().setIndex(0)
        )
        self.online_translate_and_replace_the_selected_text_shortcut_set_default.clicked.connect(
            lambda: self.online_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                "ctrl + alt + ["
            )
        )
        self.use_search_selected_text_with_everything_function.toggled.connect(
            lambda: self.use_search_selected_text_with_everything_function_changed()
        )
        self.search_selected_text_with_everything_shortcut_set_default.clicked.connect(
            lambda: self.search_selected_text_with_everything_shortcut.lineEdit().setText(
                "ctrl + alt + f"
            )
        )
        self.save.longPressed.connect(self.save_config)
        # 数据校验绑定
        self.addr.lineEdit().editingFinished.connect(self.validate_addr)
        self.save.clicked.connect(self.validate_addr)
        self.save.clicked.connect(lambda: self.validate_vscode_exe_path(on_save=True))
        self.speech_recognition_shortcut.lineEdit().editingFinished.connect(
            self.validate_speech_recognition_shortcut
        )
        self.save.clicked.connect(self.validate_speech_recognition_shortcut)
        self.start_music_path.lineEdit().editingFinished.connect(
            self.validate_start_music_path
        )
        self.save.clicked.connect(self.validate_start_music_path)
        self.stop_music_path.lineEdit().editingFinished.connect(
            self.validate_stop_music_path
        )
        self.save.clicked.connect(self.validate_stop_music_path)
        self.offline_translate_shortcut.lineEdit().editingFinished.connect(
            self.validate_offline_translate_shortcut
        )
        self.save.clicked.connect(self.validate_offline_translate_shortcut)
        self.offline_translate_and_replace_the_selected_text_shortcut.lineEdit().editingFinished.connect(
            self.validate_offline_translate_and_replace_the_selected_text_shortcut
        )
        self.save.clicked.connect(
            self.validate_offline_translate_and_replace_the_selected_text_shortcut
        )
        self.online_translate_shortcut.lineEdit().editingFinished.connect(
            self.validate_online_translate_shortcut
        )
        self.save.clicked.connect(self.validate_online_translate_shortcut)
        self.online_translate_and_replace_the_selected_text_shortcut.lineEdit().editingFinished.connect(
            self.validate_online_translate_and_replace_the_selected_text_shortcut
        )
        self.save.clicked.connect(
            self.validate_online_translate_and_replace_the_selected_text_shortcut
        )
        self.search_selected_text_with_everything_shortcut.lineEdit().editingFinished.connect(
            self.validate_search_selected_text_with_everything_shortcut
        )
        self.save.clicked.connect(
            self.validate_search_selected_text_with_everything_shortcut
        )

    def validate_addr(self):
        ip: str = self.addr.lineEdit().text()
        is_valid, error = ValueCheck.is_local_listenable_ip(ip)
        from rich import print

        if is_valid:
            print(f"[green]{ip}[/green]")
        else:
            print(f"[red]{ip} - {error if error else '无效'}[/red]")

        if error:
            self.addr.lineEdit().setText("127.0.0.1")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="要连接的服务端地址格式错误",
                    text=f'{ip} - {error}\n已修改为默认值："127.0.0.1"',
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_vscode_exe_path(self, on_save: bool = False):
        if not on_save:
            if not self.vscode_exe_path:
                return
        else:
            if not self.config_path:
                self.vscode_exe_path_selector.path_input.lineEdit().setText("")
                self.vscode_exe_path = ""
        is_valid, error = ValueCheck.is_file_exist(self.vscode_exe_path, ".exe")
        from rich import print

        if is_valid:
            print(f"[green]{self.vscode_exe_path}[/green]")
        else:
            print(f"[red]{self.vscode_exe_path} - {error if error else '无效'}[/red]")

        if error:
            self.vscode_exe_path_selector.path_input.lineEdit().setText("")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="VSCode 可执行文件位置错误",
                    text=f"{self.vscode_exe_path} - {error}\n已清空，请重新设置\n或者不使用 🤓 Open Home Folder With VSCode 功能",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_speech_recognition_shortcut(self):
        shortcut: str = self.speech_recognition_shortcut.lineEdit().text()
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.speech_recognition_shortcut.lineEdit().setText("caps lock")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="语音识别快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“caps lock”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_start_music_path(self):
        path: str = self.start_music_path.lineEdit().text()
        is_valid, error = ValueCheck.is_file_exist(path, ".mp3")
        from rich import print

        if is_valid:
            print(f"[green]{path}[/green]")
        else:
            print(f"[red]{path} - {error if error else '无效'}[/red]")

        if error:
            self.start_music_path.lineEdit().setText("assets/start.mp3")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="启动音乐文件位置错误",
                    text=f"{path} - {error}\n已修改为默认值：“assets/start.mp3”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_stop_music_path(self):
        path: str = self.stop_music_path.lineEdit().text()
        is_valid, error = ValueCheck.is_file_exist(path, ".mp3")
        from rich import print

        if is_valid:
            print(f"[green]{path}[/green]")
        else:
            print(f"[red]{path} - {error if error else '无效'}[/red]")

        if error:
            self.stop_music_path.lineEdit().setText("assets/stop.mp3")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="停止音乐文件位置错误",
                    text=f"{path} - {error}\n已修改为默认值：“assets/stop.mp3”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_offline_translate_shortcut(self):
        shortcut: str = self.offline_translate_shortcut.lineEdit().text()
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.offline_translate_shortcut.lineEdit().setText("left shift")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="离线翻译快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“left shift”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_offline_translate_and_replace_the_selected_text_shortcut(self):
        shortcut: str = self.offline_translate_and_replace_the_selected_text_shortcut.lineEdit().text()
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.offline_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                "ctrl + alt + p"
            )
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="离线翻译并替换选中文本快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“ctrl + alt + p”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_online_translate_shortcut(self):
        shortcut: str = self.online_translate_shortcut.lineEdit().text()
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.online_translate_shortcut.lineEdit().setText("right shift")
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="在线翻译快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“right shift”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_online_translate_and_replace_the_selected_text_shortcut(self):
        shortcut: str = self.online_translate_and_replace_the_selected_text_shortcut.lineEdit().text()
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.online_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                "ctrl + alt + ["
            )
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="在线翻译并替换选中文本快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“ctrl + alt + [”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def validate_search_selected_text_with_everything_shortcut(self):
        shortcut: str = (
            self.search_selected_text_with_everything_shortcut.lineEdit().text()
        )
        is_valid, error = ValueCheck.is_hotkey(shortcut)
        from rich import print

        if is_valid:
            print(f"[green]{shortcut}[/green]")
        else:
            print(f"[red]{shortcut} - {error if error else '无效'}[/red]")

        if error:
            self.search_selected_text_with_everything_shortcut.lineEdit().setText(
                "ctrl + alt + f"
            )
            try:
                SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                    title="搜索选中文本与 Everything 快捷键格式错误",
                    text=f"{shortcut} - {error}\n已修改为默认值：“ctrl + alt + f”",
                    msg_type=3,
                    icon=SiGlobal.siui.iconpack.get("ic_fluent_warning_regular"),
                    fold_after=5000,
                )
            except ValueError:
                pass

    def init_ui(self):
        self.setPadding(64)
        self.setScrollMaximumWidth(1000)
        self.setScrollAlignment(Qt.AlignLeft)
        self.setTitle("客户端配置")

        # 创建控件组
        self.titled_widgets_group = SiTitledWidgetGroup(self)
        self.titled_widgets_group.setSpacing(32)
        self.titled_widgets_group.setAdjustWidgetsSize(True)

        # 保存配置按钮
        with self.titled_widgets_group as group:
            self.save = SiLongPressButtonRefactor(self)
            self.save.setSvgIcon(SiGlobal.siui.iconpack.get("ic_fluent_save_filled"))
            self.save.setIconSize(QSize(32, 32))
            self.save.setText("\t保存 客户端 配置")
            self.save.setFont(QFont("Microsoft YaHei", 16))
            self.save.setToolTip(
                "点击按钮进行数据格式检查\n长按以确认将数据写入配置文件\n保存配置后请手动重启 服务端/客户端 以加载新配置生效"
            )
            self.save.resize(420, 64)
            self.save_container = SiDenseVContainer(self)
            self.save_container.setAlignment(Qt.AlignCenter)
            self.save_container.addWidget(self.save)
            group.addWidget(self.save_container)

        with self.titled_widgets_group as group:
            group.addTitle("通用")

            # 要连接的服务端地址
            self.addr = SiLineEditWithDeletionButton(self)
            self.addr.resize(256, 32)
            self.addr.lineEdit().setText(self.config["client"]["addr"])
            self.addr_set_default = SetDefaultButton(self)
            self.addr_linear_attaching = SiOptionCardLinear(self)
            self.addr_linear_attaching.setTitle(
                "要连接的服务端地址", '默认值："127.0.0.1" 本地地址'
            )
            self.addr_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.addr_linear_attaching.addWidget(self.addr_set_default)
            self.addr_linear_attaching.addWidget(self.addr)

            # 启动后是否自动缩小至托盘
            self.shrink_automatically_to_tray = SiSwitch(self)
            self.shrink_automatically_to_tray.setChecked(
                self.config["client"]["shrink_automatically_to_tray"]
            )
            self.shrink_automatically_to_tray_linear_attaching = SiOptionCardLinear(
                self
            )
            self.shrink_automatically_to_tray_linear_attaching.setTitle(
                "启动后自动缩小至托盘"
            )
            self.shrink_automatically_to_tray_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_phone_footer_arrow_down_regular")
            )
            self.shrink_automatically_to_tray_linear_attaching.addWidget(
                self.shrink_automatically_to_tray
            )

            # 只允许运行一次，禁止多开
            self.only_run_once = SiSwitch(self)
            self.only_run_once.setChecked(self.config["client"]["only_run_once"])
            self.only_run_once_linear_attaching = SiOptionCardLinear(self)
            self.only_run_once_linear_attaching.setTitle("禁止多开", "只允许运行一次")
            self.only_run_once_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_star_one_quarter_filled")
            )
            self.only_run_once_linear_attaching.addWidget(self.only_run_once)

            # 设置 VSCode 可执行文件位置
            # 用于通过客户端托盘图标右键菜单项 View 子菜单项
            # 🤓 Open Home Folder With VSCode
            # 使用 VSCode 快速打开 CapsWriter 主目录
            # 方便调试
            self.vscode_exe_path_selector = SelectPath(
                self,
                title="VSCode 可执行文件位置",
                label_text="用于通过客户端托盘图标右键菜单项 View 子菜单项 “🤓 Open Home Folder With VSCode”\n使用 VSCode 快速打开 CapsWriter 主目录\n方便调试",
                default_path=self.config["client"]["vscode_exe_path"],
                file_filter="Executables (*.exe)",
                mode="file",
            )

            # 设置项
            self.general_container = SiDenseVContainer(self)
            self.general_container.setFixedWidth(700)
            self.general_container.setAdjustWidgetsSize(True)
            self.general_container.addWidget(self.addr_linear_attaching)
            self.general_container.addWidget(
                self.shrink_automatically_to_tray_linear_attaching
            )
            self.general_container.addWidget(self.only_run_once_linear_attaching)
            self.general_container.addWidget(self.vscode_exe_path_selector)
            group.addWidget(self.general_container)

        with self.titled_widgets_group as group:
            group.addTitle("语音识别")

            # 控制录音的快捷键，默认是 "caps lock"
            self.speech_recognition_shortcut = SiLineEditWithDeletionButton(self)
            self.speech_recognition_shortcut.resize(256, 32)
            self.speech_recognition_shortcut.lineEdit().setText(
                self.config["client"]["speech_recognition_shortcut"]
            )
            self.speech_recognition_shortcut_set_default = SetDefaultButton(self)
            self.speech_recognition_shortcut_linear_attaching = SiOptionCardLinear(self)
            self.speech_recognition_shortcut_linear_attaching.setTitle(
                "控制录音的快捷键", '默认值："caps lock"'
            )
            self.speech_recognition_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.speech_recognition_shortcut_linear_attaching.addWidget(
                self.speech_recognition_shortcut_set_default
            )
            self.speech_recognition_shortcut_linear_attaching.addWidget(
                self.speech_recognition_shortcut
            )
            # 只在按下录音快捷键时启用麦克风
            # 建议启用，有些蓝牙耳机录音时无法播放
            # 而且启用后，切换默认麦克风也不用重启客户端
            # 比如从蓝牙耳机换回笔记本电脑默认麦克风
            # 缺点就是输入的时候可能会慢些
            # 毕竟要先建立与麦克风的连接
            self.only_enable_microphones_when_pressed_record_shortcut = SiSwitch(self)
            self.only_enable_microphones_when_pressed_record_shortcut.setChecked(
                self.config["client"][
                    "only_enable_microphones_when_pressed_record_shortcut"
                ]
            )
            self.only_enable_microphones_when_pressed_record_shortcut_linear_attaching = SiOptionCardLinear(
                self
            )
            self.only_enable_microphones_when_pressed_record_shortcut_linear_attaching.setTitle(
                "只在按下录音快捷键时启用麦克风",
                "建议启用\n有些蓝牙耳机录音时无法播放\n而且启用后\n切换默认麦克风也不用重启客户端\n比如从蓝牙耳机换回笔记本电脑默认麦克风\n缺点就是输入的时候可能会慢些\n毕竟要先建立与麦克风的连接",
            )
            self.only_enable_microphones_when_pressed_record_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_mic_record_regular")
            )
            self.only_enable_microphones_when_pressed_record_shortcut_linear_attaching.addWidget(
                self.only_enable_microphones_when_pressed_record_shortcut
            )

            # 语音识别服务端口
            self.speech_recognition_port = SiIntSpinBox(self)
            self.speech_recognition_port.resize(256, 32)
            self.speech_recognition_port.setMinimum(1024)
            self.speech_recognition_port.setMaximum(65535)
            self.speech_recognition_port.setValue(
                int(self.config["client"]["speech_recognition_port"])
            )
            self.speech_recognition_port_set_default = SetDefaultButton(self)
            self.speech_recognition_port_linear_attaching = SiOptionCardLinear(self)
            self.speech_recognition_port_linear_attaching.setTitle(
                "语音识别服务端口", '默认值："6016"\n端口号范围 1024-65535'
            )
            self.speech_recognition_port_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.speech_recognition_port_linear_attaching.addWidget(
                self.speech_recognition_port_set_default
            )
            self.speech_recognition_port_linear_attaching.addWidget(
                self.speech_recognition_port
            )
            # 麦克风听写时分段长度：15 秒
            self.mic_seg_duration = SiIntSpinBox(self)
            self.mic_seg_duration.resize(256, 32)
            self.mic_seg_duration.setMinimum(10)
            self.mic_seg_duration.setMaximum(60)
            self.mic_seg_duration.setValue(self.config["client"]["mic_seg_duration"])
            self.mic_seg_duration_set_default = SetDefaultButton(self)
            self.mic_seg_duration_linear_attaching = SiOptionCardLinear(self)
            self.mic_seg_duration_linear_attaching.setTitle(
                "麦克风听写时分段长度", '默认值："15" 秒'
            )
            self.mic_seg_duration_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_timer_regular")
            )
            self.mic_seg_duration_linear_attaching.addWidget(
                self.mic_seg_duration_set_default
            )
            self.mic_seg_duration_linear_attaching.addWidget(self.mic_seg_duration)

            # 麦克风听写时分段重叠：2 秒
            self.mic_seg_overlap = SiIntSpinBox(self)
            self.mic_seg_overlap.resize(256, 32)
            self.mic_seg_overlap.setMinimum(0)
            self.mic_seg_overlap.setMaximum(10)
            self.mic_seg_overlap.setValue(self.config["client"]["mic_seg_overlap"])
            self.mic_seg_overlap_set_default = SetDefaultButton(self)
            self.mic_seg_overlap_linear_attaching = SiOptionCardLinear(self)
            self.mic_seg_overlap_linear_attaching.setTitle(
                "麦克风听写时分段重叠", '默认值："2" 秒'
            )
            self.mic_seg_overlap_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_timer_regular")
            )
            self.mic_seg_overlap_linear_attaching.addWidget(
                self.mic_seg_overlap_set_default
            )
            self.mic_seg_overlap_linear_attaching.addWidget(self.mic_seg_overlap)

            # 转录文件时分段长度：25 秒
            self.file_seg_duration = SiIntSpinBox(self)
            self.file_seg_duration.resize(256, 32)
            self.file_seg_duration.setMinimum(10)
            self.file_seg_duration.setMaximum(60)
            self.file_seg_duration.setValue(self.config["client"]["file_seg_duration"])
            self.file_seg_duration_set_default = SetDefaultButton(self)
            self.file_seg_duration_linear_attaching = SiOptionCardLinear(self)
            self.file_seg_duration_linear_attaching.setTitle(
                "转录文件时分段长度", '默认值："25" 秒'
            )
            self.file_seg_duration_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_timer_regular")
            )
            self.file_seg_duration_linear_attaching.addWidget(
                self.file_seg_duration_set_default
            )
            self.file_seg_duration_linear_attaching.addWidget(self.file_seg_duration)

            # 转录文件时分段重叠：2 秒
            self.file_seg_overlap = SiIntSpinBox(self)
            self.file_seg_overlap.resize(256, 32)
            self.file_seg_overlap.setMinimum(1)
            self.file_seg_overlap.setMaximum(60)
            self.file_seg_overlap.setValue(self.config["client"]["file_seg_overlap"])
            self.file_seg_overlap_set_default = SetDefaultButton(self)
            self.file_seg_overlap_linear_attaching = SiOptionCardLinear(self)
            self.file_seg_overlap_linear_attaching.setTitle(
                "转录文件时分段重叠", '默认值："2" 秒'
            )
            self.file_seg_overlap_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_timer_regular")
            )
            self.file_seg_overlap_linear_attaching.addWidget(
                self.file_seg_overlap_set_default
            )
            self.file_seg_overlap_linear_attaching.addWidget(self.file_seg_overlap)

            # 长按模式，按下录音，松开停止，像对讲机一样用
            # 改为 False，则关闭长按模式，也就是单击模式
            # 即：单击录音，再次单击停止
            # 且：长按会执行原本的单击功能
            self.hold_mode = SiSwitch(self)
            self.hold_mode.setChecked(self.config["client"]["hold_mode"])
            self.hold_mode_linear_attaching = SiOptionCardLinear(self)
            self.hold_mode_linear_attaching.setTitle(
                "长按模式",
                "按下录音\n松开停止\n像对讲机一样用\n改为 False\n则关闭长按模式\n也就是单击模式\n即：单击录音\n再次单击停止\n且：长按会执行原本的单击功能",
            )
            self.hold_mode_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.hold_mode_linear_attaching.addWidget(self.hold_mode)

            # 开始任务时是否播放提示音
            # 需要 ffplay.exe
            self.play_start_music = SiSwitch(self)
            self.play_start_music.setChecked(self.config["client"]["play_start_music"])
            self.play_start_music_linear_attaching = SiOptionCardLinear(self)
            self.play_start_music_linear_attaching.setTitle(
                "开始任务时播放提示音",
                '需要 ffplay.exe\n提示音路径："assets/start.mp3"',
            )
            self.play_start_music_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.play_start_music_linear_attaching.addWidget(self.play_start_music)

            # 开始任务提示音的文件路径
            self.start_music_path = SiLineEditWithDeletionButton(self)
            self.start_music_path.resize(256, 32)
            self.start_music_path.lineEdit().setText(
                self.config["client"]["start_music_path"]
            )
            self.start_music_path_set_default = SetDefaultButton(self)
            self.start_music_path_linear_attaching = SiOptionCardLinear(self)
            self.start_music_path_linear_attaching.setTitle(
                "开始任务提示音的文件路径", '默认值："assets/start.mp3"'
            )
            self.start_music_path_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.start_music_path_linear_attaching.addWidget(
                self.start_music_path_set_default
            )
            self.start_music_path_linear_attaching.addWidget(self.start_music_path)

            # 开始任务提示音的音量，0 ~ 100 之间
            self.start_music_volume = SiSlider(self)
            self.start_music_volume.resize(512, 48)
            self.start_music_volume.setMinimum(0)
            self.start_music_volume.setMaximum(100)
            self.start_music_volume.setValue(
                int(self.config["client"]["start_music_volume"])
            )
            self.start_music_volume_linear_attaching = SiOptionCardLinear(self)
            self.start_music_volume_linear_attaching.setTitle("开始任务提示音的音量")
            self.start_music_volume_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.start_music_volume_linear_attaching.addWidget(self.start_music_volume)

            # 结束任务时是否播放提示音
            # 需要 ffplay.exe
            self.play_stop_music = SiSwitch(self)
            self.play_stop_music.setChecked(self.config["client"]["play_stop_music"])
            self.play_stop_music_linear_attaching = SiOptionCardLinear(self)
            self.play_stop_music_linear_attaching.setTitle(
                "结束任务时播放提示音",
                '需要 ffplay.exe\n提示音路径："assets/stop.mp3"',
            )
            self.play_stop_music_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.play_stop_music_linear_attaching.addWidget(self.play_stop_music)

            # 结束任务提示音的文件路径
            self.stop_music_path = SiLineEditWithDeletionButton(self)
            self.stop_music_path.resize(256, 32)
            self.stop_music_path.lineEdit().setText(
                self.config["client"]["stop_music_path"]
            )
            self.stop_music_path_set_default = SetDefaultButton(self)
            self.stop_music_path_linear_attaching = SiOptionCardLinear(self)
            self.stop_music_path_linear_attaching.setTitle(
                "结束任务提示音的文件路径", '默认值："assets/stop.mp3"'
            )
            self.stop_music_path_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.stop_music_path_linear_attaching.addWidget(
                self.stop_music_path_set_default
            )
            self.stop_music_path_linear_attaching.addWidget(self.stop_music_path)

            # 结束任务提示音的音量，0 ~ 100 之间
            self.stop_music_volume = SiSlider(self)
            self.stop_music_volume.resize(512, 48)
            self.stop_music_volume.setMinimum(0)
            self.stop_music_volume.setMaximum(100)
            self.stop_music_volume.setValue(
                int(self.config["client"]["stop_music_volume"])
            )
            self.stop_music_volume_linear_attaching = SiOptionCardLinear(self)
            self.stop_music_volume_linear_attaching.setTitle("结束任务提示音的音量")
            self.stop_music_volume_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_music_note_1_filled")
            )
            self.stop_music_volume_linear_attaching.addWidget(self.stop_music_volume)

            # 录音时是否静音其他音频播放
            self.mute_other_audio = SiSwitch(self)
            self.mute_other_audio.setChecked(self.config["client"]["mute_other_audio"])
            self.mute_other_audio_linear_attaching = SiOptionCardLinear(self)
            self.mute_other_audio_linear_attaching.setTitle(
                "录音时静音其他音频播放",
            )
            self.mute_other_audio_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_speaker_mute_regular")
            )
            self.mute_other_audio_linear_attaching.addWidget(self.mute_other_audio)

            # 录音时是否暂停其他音频播放
            self.pause_other_audio = SiSwitch(self)
            self.pause_other_audio.setChecked(
                self.config["client"]["pause_other_audio"]
            )
            self.pause_other_audio_linear_attaching = SiOptionCardLinear(self)
            self.pause_other_audio_linear_attaching.setTitle(
                "录音时暂停其他音频播放",
            )
            self.pause_other_audio_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_pause_regular")
            )
            self.pause_other_audio_linear_attaching.addWidget(self.pause_other_audio)

            # 是否启用基于 AHK 的输入光标位置的输入状态提示功能
            self.hint_while_recording_at_edit_position_powered_by_ahk = SiSwitch(self)
            self.hint_while_recording_at_edit_position_powered_by_ahk.setChecked(
                self.config["client"][
                    "hint_while_recording_at_edit_position_powered_by_ahk"
                ]
            )
            self.hint_while_recording_at_edit_position_powered_by_ahk_linear_attaching = SiOptionCardLinear(
                self
            )
            self.hint_while_recording_at_edit_position_powered_by_ahk_linear_attaching.setTitle(
                "在输入光标位置显示 “✦语音输入中‧‧‧” 状态提示",
                "基于 AHK 的输入光标位置的输入状态提示功能\n更多相关配置在 “hint_while_recording.ini” ",
            )
            self.hint_while_recording_at_edit_position_powered_by_ahk_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_emoji_hint_regular")
            )
            self.hint_while_recording_at_edit_position_powered_by_ahk_linear_attaching.addWidget(
                self.hint_while_recording_at_edit_position_powered_by_ahk
            )

            # 是否启用跟随鼠标光标位置的新版输入状态提示功能
            self.hint_while_recording_at_cursor_position = SiSwitch(self)
            self.hint_while_recording_at_cursor_position.setChecked(
                self.config["client"]["hint_while_recording_at_cursor_position"]
            )
            self.hint_while_recording_at_cursor_position_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.hint_while_recording_at_cursor_position_linear_attaching.setTitle(
                "在鼠标光标位置显示 麦克风图案 的输入状态提示", "基于 Python PySide6"
            )
            self.hint_while_recording_at_cursor_position_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_emoji_hint_regular")
            )
            self.hint_while_recording_at_cursor_position_linear_attaching.addWidget(
                self.hint_while_recording_at_cursor_position
            )

            # 监测麦克风是否在使用的方式
            # "按键" 或 "注册表"
            self.check_microphone_usage_by = SiComboBox(self)
            self.check_microphone_usage_by.resize(325, 32)
            self.check_microphone_usage_by.addOption("注册表")
            self.check_microphone_usage_by.addOption("按键")
            self.check_microphone_usage_by.menu().setShowIcon(False)
            if self.config["client"]["check_microphone_usage_by"] == "注册表":
                self.check_microphone_usage_by.menu().setIndex(0)
            else:
                self.check_microphone_usage_by.menu().setIndex(1)
            self.check_microphone_usage_by_linear_attaching = SiOptionCardLinear(self)
            self.check_microphone_usage_by_linear_attaching.setTitle(
                "监测麦克风是否在使用的方式",
                "按键：通过按下录音快捷键来检测麦克风是否在使用\n注册表：通过读取注册表来检测麦克风是否在使用",
            )
            self.check_microphone_usage_by_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_settings_light")
            )
            self.check_microphone_usage_by_linear_attaching.addWidget(
                self.check_microphone_usage_by
            )

            # 是否阻塞按键事件（让其它程序收不到这个按键消息）
            self.suppress = SiSwitch(self)
            self.suppress.setChecked(self.config["client"]["suppress"])
            self.suppress_linear_attaching = SiOptionCardLinear(self)
            self.suppress_linear_attaching.setTitle(
                "阻塞按键事件",
                "如果开启\n则按下录音快捷键后\n其它程序无法接收到这个按键消息",
            )
            self.suppress_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.suppress_linear_attaching.addWidget(self.suppress)

            # 录音完成，松开按键后，是否自动再按一遍，以恢复 CapsLock 或 Shift 等按键之前的状态
            self.restore_key = SiSwitch(self)
            self.restore_key.setChecked(self.config["client"]["restore_key"])
            self.restore_key_linear_attaching = SiOptionCardLinear(self)
            self.restore_key_linear_attaching.setTitle(
                "恢复按键状态",
                "录音完成\n松开按键后\n是否自动再按一遍\n以恢复 CapsLock 或 Shift 等按键之前的状态",
            )
            self.restore_key_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.restore_key_linear_attaching.addWidget(self.restore_key)

            # 按下快捷键后，触发语音识别的时间阈值
            self.threshold = SiDoubleSpinBox(self)
            self.threshold.resize(256, 32)
            self.threshold.setMinimum(0.1)
            self.threshold.setMaximum(2.0)
            self.threshold.setSingleStep(0.1)
            self.threshold.setValue(self.config["client"]["threshold"])
            self.threshold_set_default = SetDefaultButton(self)
            self.threshold_linear_attaching = SiOptionCardLinear(self)
            self.threshold_linear_attaching.setTitle(
                "触发语音识别的时间阈值",
                "按下快捷键后\n触发语音识别的时间阈值\n单位：秒\n默认值：0.3 秒\n如果设置的值过小\n可能会造成误触发",
            )
            self.threshold_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_timer_regular")
            )
            self.threshold_linear_attaching.addWidget(self.threshold_set_default)
            self.threshold_linear_attaching.addWidget(self.threshold)

            # 识别结果要消除的末尾标点
            self.trash_punc = SiLineEditWithDeletionButton(self)
            self.trash_punc.resize(256, 32)
            self.trash_punc.lineEdit().setText(self.config["client"]["trash_punc"])
            self.trash_punc_set_default = SetDefaultButton(self)
            self.trash_punc_linear_attaching = SiOptionCardLinear(self)
            self.trash_punc_linear_attaching.setTitle(
                "识别结果要消除的末尾标点",
                '识别结果要消除的末尾标点\n默认值："，。,."',
            )
            self.trash_punc_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_delete_regular")
            )
            self.trash_punc_linear_attaching.addWidget(self.trash_punc_set_default)
            self.trash_punc_linear_attaching.addWidget(self.trash_punc)

            # 是否启用中文热词替换，中文热词存储在 hot_zh.txt 文件里
            self.hot_zh = SiSwitch(self)
            self.hot_zh.setChecked(self.config["client"]["hot_zh"])
            self.hot_zh_linear_attaching = SiOptionCardLinear(self)
            self.hot_zh_linear_attaching.setTitle(
                "中文热词替换",
                "中文热词存储在 hot_zh.txt 文件里",
            )
            self.hot_zh_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.hot_zh_linear_attaching.addWidget(self.hot_zh)

            # 多音字匹配
            self.多音字 = SiSwitch(self)
            self.多音字.setChecked(self.config["client"]["多音字"])
            self.多音字_linear_attaching = SiOptionCardLinear(self)
            self.多音字_linear_attaching.setTitle(
                "多音字匹配",
                "在识别结果中匹配多音字",
            )
            self.多音字_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.多音字_linear_attaching.addWidget(self.多音字)

            # 声调匹配
            self.声调 = SiSwitch(self)
            self.声调.setChecked(self.config["client"]["声调"])
            self.声调_linear_attaching = SiOptionCardLinear(self)
            self.声调_linear_attaching.setTitle(
                "声调匹配",
                "例如：如果启用，「黄章」就能匹配「慌张」",
            )
            self.声调_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.声调_linear_attaching.addWidget(self.声调)

            # 将 ****年 大写汉字替换为阿拉伯数字 ****年，例如一八四八年 替换为 1848 年
            self.arabic_year_number = SiSwitch(self)
            self.arabic_year_number.setChecked(
                self.config["client"]["arabic_year_number"]
            )
            self.arabic_year_number_linear_attaching = SiOptionCardLinear(self)
            self.arabic_year_number_linear_attaching.setTitle(
                "将年份数字替换为阿拉伯数字",
                "例如：一八四八年 替换为 1848 年",
            )
            self.arabic_year_number_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.arabic_year_number_linear_attaching.addWidget(self.arabic_year_number)

            # 是否启用英文热词替换，英文热词存储在 hot_en.txt 文件里
            self.hot_en = SiSwitch(self)
            self.hot_en.setChecked(self.config["client"]["hot_en"])
            self.hot_en_linear_attaching = SiOptionCardLinear(self)
            self.hot_en_linear_attaching.setTitle(
                "英文热词替换",
                "英文热词存储在 hot_en.txt 文件里",
            )
            self.hot_en_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.hot_en_linear_attaching.addWidget(self.hot_en)

            # 是否启用自定义规则替换，自定义规则存储在 hot_rule.txt 文件里
            self.hot_rule = SiSwitch(self)
            self.hot_rule.setChecked(self.config["client"]["hot_rule"])
            self.hot_rule_linear_attaching = SiOptionCardLinear(self)
            self.hot_rule_linear_attaching.setTitle(
                "自定义规则替换",
                "自定义规则存储在 hot_rule.txt 文件里",
            )
            self.hot_rule_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_ruler_regular")
            )
            self.hot_rule_linear_attaching.addWidget(self.hot_rule)

            # 是否启用关键词日记功能，自定义关键词存储在 keyword.txt 文件里
            self.hot_kwd = SiSwitch(self)
            self.hot_kwd.setChecked(self.config["client"]["hot_kwd"])
            self.hot_kwd_linear_attaching = SiOptionCardLinear(self)
            self.hot_kwd_linear_attaching.setTitle(
                "启用关键词日记功能",
                "自定义关键词存储在 keyword.txt 文件里",
            )
            self.hot_kwd_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_note_edit_regular")
            )
            self.hot_kwd_linear_attaching.addWidget(self.hot_kwd)

            # 是否以写入剪切板然后模拟 Ctrl-V 粘贴的方式输出结果
            self.paste = SiSwitch(self)
            self.paste.setChecked(self.config["client"]["paste"])
            self.paste_linear_attaching = SiOptionCardLinear(self)
            self.paste_linear_attaching.setTitle(
                "以写入剪切板然后模拟 Ctrl-V 粘贴的方式输出结果",
                "如果关闭，则以模拟键盘输入的方式输出结果",
            )
            self.paste_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_clipboard_paste_filled")
            )
            self.paste_linear_attaching.addWidget(self.paste)

            # 模拟粘贴后是否恢复剪贴板
            self.restore_clipboard_after_paste = SiSwitch(self)
            self.restore_clipboard_after_paste.setChecked(
                self.config["client"]["restore_clipboard_after_paste"]
            )
            self.restore_clipboard_after_paste_linear_attaching = SiOptionCardLinear(
                self
            )
            self.restore_clipboard_after_paste_linear_attaching.setTitle(
                "模拟粘贴后是否恢复剪贴板"
            )
            self.restore_clipboard_after_paste_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_clipboard_paste_filled")
            )
            self.restore_clipboard_after_paste_linear_attaching.addWidget(
                self.restore_clipboard_after_paste
            )

            # 是否保存录音文件
            self.save_audio = SiSwitch(self)
            self.save_audio.setChecked(self.config["client"]["save_audio"])
            self.save_audio_linear_attaching = SiOptionCardLinear(self)
            self.save_audio_linear_attaching.setTitle("保存录音文件到本地磁盘")
            self.save_audio_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_save_regular")
            )
            self.save_audio_linear_attaching.addWidget(self.save_audio)

            # 将录音识别结果的前多少个字存储到录音文件名中，建议不要超过 200
            self.audio_name_len = SiIntSpinBox(self)
            self.audio_name_len.resize(256, 32)
            self.audio_name_len.setMinimum(10)
            self.audio_name_len.setMaximum(200)
            self.audio_name_len.setValue(self.config["client"]["audio_name_len"])
            self.audio_name_len_set_default = SetDefaultButton(self)
            self.audio_name_len_linear_attaching = SiOptionCardLinear(self)
            self.audio_name_len_linear_attaching.setTitle(
                "录音文件名长度",
                "将录音识别结果的前多少个字存储到录音文件名中\n建议不要超过 200",
            )
            self.audio_name_len_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_document_text_regular")
            )
            self.audio_name_len_linear_attaching.addWidget(
                self.audio_name_len_set_default
            )
            self.audio_name_len_linear_attaching.addWidget(self.audio_name_len)

            # 如果用户已安装 ffmpeg，调用 ffmpeg 录音时输出 mp3 格式的音频文件，大大减小文件体积，减少磁盘占用
            self.reduce_audio_files = SiSwitch(self)
            self.reduce_audio_files.setChecked(
                self.config["client"]["reduce_audio_files"]
            )
            self.reduce_audio_files_linear_attaching = SiOptionCardLinear(self)
            self.reduce_audio_files_linear_attaching.setTitle(
                "使用 ffmpeg 压缩录音文件",
                "如果用户已安装 ffmpeg\n调用 ffmpeg 录音时输出 mp3 格式的音频文件\n大大减小文件体积\n减少磁盘占用",
            )
            self.reduce_audio_files_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_folder_zip_regular")
            )
            self.reduce_audio_files_linear_attaching.addWidget(self.reduce_audio_files)

            # 是否将记录写入 Markdown 文件
            self.save_markdown = SiSwitch(self)
            self.save_markdown.setChecked(self.config["client"]["save_markdown"])
            self.save_markdown_linear_attaching = SiOptionCardLinear(self)
            self.save_markdown_linear_attaching.setTitle("将记录写入 Markdown 文件")
            self.save_markdown_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_save_regular")
            )
            self.save_markdown_linear_attaching.addWidget(self.save_markdown)

            # 设置项
            self.speech_recognition_container = SiDenseVContainer(self)
            self.speech_recognition_container.setFixedWidth(700)
            self.speech_recognition_container.setAdjustWidgetsSize(True)
            self.speech_recognition_container.addWidget(
                self.speech_recognition_shortcut_linear_attaching
            )

            self.speech_recognition_container.addWidget(
                self.only_enable_microphones_when_pressed_record_shortcut_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.speech_recognition_port_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.mic_seg_duration_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.mic_seg_overlap_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.file_seg_duration_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.file_seg_overlap_linear_attaching
            )
            self.speech_recognition_container.addWidget(self.hold_mode_linear_attaching)
            self.hold_mode_changed()
            self.speech_recognition_container.addWidget(
                self.play_start_music_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.start_music_path_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.start_music_volume_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.play_stop_music_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.stop_music_path_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.stop_music_volume_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.mute_other_audio_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.pause_other_audio_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.hint_while_recording_at_edit_position_powered_by_ahk_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.hint_while_recording_at_cursor_position_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.check_microphone_usage_by_linear_attaching
            )
            self.speech_recognition_container.addWidget(self.suppress_linear_attaching)
            self.speech_recognition_container.addWidget(
                self.restore_key_linear_attaching
            )
            self.speech_recognition_container.addWidget(self.threshold_linear_attaching)
            self.speech_recognition_container.addWidget(
                self.trash_punc_linear_attaching
            )
            self.speech_recognition_container.addWidget(self.hot_zh_linear_attaching)
            self.speech_recognition_container.addWidget(self.多音字_linear_attaching)
            self.speech_recognition_container.addWidget(self.声调_linear_attaching)
            self.speech_recognition_container.addWidget(
                self.arabic_year_number_linear_attaching
            )
            self.speech_recognition_container.addWidget(self.hot_en_linear_attaching)
            self.speech_recognition_container.addWidget(self.hot_rule_linear_attaching)
            self.speech_recognition_container.addWidget(self.hot_kwd_linear_attaching)
            self.speech_recognition_container.addWidget(self.paste_linear_attaching)
            self.paste_changed()
            self.speech_recognition_container.addWidget(
                self.restore_clipboard_after_paste_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.save_audio_linear_attaching
            )
            self.save_audio_changed()
            self.speech_recognition_container.addWidget(
                self.audio_name_len_linear_attaching
            )
            self.speech_recognition_container.addWidget(
                self.reduce_audio_files_linear_attaching
            )

            self.speech_recognition_container.addWidget(
                self.save_markdown_linear_attaching
            )
            group.addWidget(self.speech_recognition_container)

        with self.titled_widgets_group as group:
            group.addTitle("简繁转换")

            # 默认使用简/繁体中文作为主要输出
            self.convert_to_traditional_chinese_main = SiToggleButtonRefactor(self)
            if self.config["client"]["convert_to_traditional_chinese_main"] == "简":
                self.convert_to_traditional_chinese_main.setChecked(False)
            else:
                self.convert_to_traditional_chinese_main.setChecked(True)
            # self.convert_to_traditional_chinese_main.adjustSize()
            self.convert_to_traditional_chinese_main.setFont(
                QFont("Microsoft YaHei", 16)
            )
            self.convert_to_traditional_chinese_main.resize(100, 50)
            self.convert_to_traditional_chinese_main_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.convert_to_traditional_chinese_main_linear_attaching.setTitle(
                "默认使用简/繁体中文作为主要输出"
            )
            self.convert_to_traditional_chinese_main_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_translate_auto_regular")
            )
            self.convert_to_traditional_chinese_main_linear_attaching.addWidget(
                self.convert_to_traditional_chinese_main
            )
            # 是否启用双击 `录音键` 临时转换 `简/繁` 体中文输出的功能
            self.enable_double_click_opposite_state = SiSwitch(self)
            self.enable_double_click_opposite_state.setChecked(
                self.config["client"]["enable_double_click_opposite_state"]
            )
            self.enable_double_click_opposite_state_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.enable_double_click_opposite_state_linear_attaching.setTitle(
                "双击 `录音键` 临时转换 `简/繁` 体中文输出的功能"
            )
            self.enable_double_click_opposite_state_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_translate_auto_regular")
            )
            self.enable_double_click_opposite_state_linear_attaching.addWidget(
                self.enable_double_click_opposite_state
            )

            # 设置项
            self.convert_to_traditional_chinese_container = SiDenseVContainer(self)
            self.convert_to_traditional_chinese_container.setFixedWidth(700)
            self.convert_to_traditional_chinese_container.setAdjustWidgetsSize(True)
            self.convert_to_traditional_chinese_container.addWidget(
                self.convert_to_traditional_chinese_main_linear_attaching
            )
            self.convert_to_traditional_chinese_main_changed()
            self.convert_to_traditional_chinese_container.addWidget(
                self.enable_double_click_opposite_state_linear_attaching
            )
            group.addWidget(self.convert_to_traditional_chinese_container)

        with self.titled_widgets_group as group:
            group.addTitle("离线翻译")

            # 是否启用离线翻译功能
            self.use_offline_translate_function = SiSwitch(self)
            self.use_offline_translate_function.setChecked(
                self.config["client"]["use_offline_translate_function"]
            )
            self.use_offline_translate_function_linear_attaching = SiOptionCardLinear(
                self
            )
            self.use_offline_translate_function_linear_attaching.setTitle(
                "启用离线翻译功能"
            )
            self.use_offline_translate_function_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_translate_auto_regular")
            )
            self.use_offline_translate_function_linear_attaching.addWidget(
                self.use_offline_translate_function
            )
            # 离线翻译服务端口
            self.offline_translate_port = SiIntSpinBox(self)
            self.offline_translate_port.resize(256, 32)
            self.offline_translate_port.setMinimum(1024)
            self.offline_translate_port.setMaximum(65535)
            self.offline_translate_port.setValue(
                int(self.config["client"]["offline_translate_port"])
            )
            self.offline_translate_port_set_default = SetDefaultButton(self)
            self.offline_translate_port_linear_attaching = SiOptionCardLinear(self)
            self.offline_translate_port_linear_attaching.setTitle(
                "离线翻译服务端口", '默认值："6017"\n端口号范围 1024-65535'
            )
            self.offline_translate_port_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_globe_location_regular")
            )
            self.offline_translate_port_linear_attaching.addWidget(
                self.offline_translate_port_set_default
            )
            self.offline_translate_port_linear_attaching.addWidget(
                self.offline_translate_port
            )
            # 控制离线翻译的快捷键，默认是 "left shift"，按住 Left Shift 再按 CapsLock 进行离线翻译
            self.offline_translate_shortcut = SiLineEditWithDeletionButton(self)
            self.offline_translate_shortcut.resize(256, 32)
            self.offline_translate_shortcut.lineEdit().setText(
                self.config["client"]["offline_translate_shortcut"]
            )
            self.offline_translate_shortcut_set_default = SetDefaultButton(self)
            self.offline_translate_shortcut_linear_attaching = SiOptionCardLinear(self)
            self.offline_translate_shortcut_linear_attaching.setTitle(
                "离线翻译的快捷键",
                '默认值："left shift"\n按住 Left Shift 再按 CapsLock 进行离线翻译',
            )
            self.offline_translate_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.offline_translate_shortcut_linear_attaching.addWidget(
                self.offline_translate_shortcut_set_default
            )
            self.offline_translate_shortcut_linear_attaching.addWidget(
                self.offline_translate_shortcut
            )
            # 控制离线翻译将光标选中的中文翻译并替换为英文的快捷键
            # 如果未选中任何文字，会将剪贴板的文字翻译为英文并粘贴
            self.offline_translate_and_replace_the_selected_text_shortcut = (
                SiLineEditWithDeletionButton(self)
            )
            self.offline_translate_and_replace_the_selected_text_shortcut.resize(
                256, 32
            )
            self.offline_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                self.config["client"][
                    "offline_translate_and_replace_the_selected_text_shortcut"
                ]
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_set_default = SetDefaultButton(
                self
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching = SiOptionCardLinear(
                self
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.setTitle(
                "将光标选中的中文翻译并替换为英文的快捷键",
                '默认值："ctrl + alt + p"\n未选中任何文字时\n将剪贴板的文字翻译为英文并粘贴',
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.addWidget(
                self.offline_translate_and_replace_the_selected_text_shortcut_set_default
            )
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.addWidget(
                self.offline_translate_and_replace_the_selected_text_shortcut
            )

            # 设置项
            self.offline_translate_container = SiDenseVContainer(self)
            self.offline_translate_container.setFixedWidth(700)
            self.offline_translate_container.setAdjustWidgetsSize(True)
            self.offline_translate_container.addWidget(
                self.use_offline_translate_function_linear_attaching
            )
            self.use_offline_translate_function_changed()
            self.offline_translate_container.addWidget(
                self.offline_translate_port_linear_attaching
            )
            self.offline_translate_container.addWidget(
                self.offline_translate_shortcut_linear_attaching
            )
            self.offline_translate_container.addWidget(
                self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching
            )
            group.addWidget(self.offline_translate_container)

        with self.titled_widgets_group as group:
            group.addTitle("在线翻译")

            # 是否启用在线翻译功能
            self.use_online_translate_function = SiSwitch(self)
            self.use_online_translate_function.setChecked(
                self.config["client"]["use_online_translate_function"]
            )
            self.use_online_translate_function_linear_attaching = SiOptionCardLinear(
                self
            )
            self.use_online_translate_function_linear_attaching.setTitle(
                "启用在线翻译功能"
            )
            self.use_online_translate_function_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_translate_regular")
            )
            self.use_online_translate_function_linear_attaching.addWidget(
                self.use_online_translate_function
            )
            # 控制在线翻译的快捷键，默认是 Right Shift，按住 Right Shift 再按 CapsLock 进行在线翻译
            # 在线翻译基于 DeepLX，过于频繁的请求可能导致 IP 被封
            # 如果出现 429 错误，则表示你的 IP 被 DeepL 暂时屏蔽了，请不要在短时间内频繁请求
            self.online_translate_shortcut = SiLineEditWithDeletionButton(self)
            self.online_translate_shortcut.resize(256, 32)
            self.online_translate_shortcut.lineEdit().setText(
                self.config["client"]["online_translate_shortcut"]
            )
            self.online_translate_shortcut_set_default = SetDefaultButton(self)
            self.online_translate_shortcut_linear_attaching = SiOptionCardLinear(self)
            self.online_translate_shortcut_linear_attaching.setTitle(
                "在线翻译的快捷键",
                '默认值："right shift"\n按住 Right Shift 再按 CapsLock 进行在线翻译',
            )
            self.online_translate_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.online_translate_shortcut_linear_attaching.addWidget(
                self.online_translate_shortcut_set_default
            )
            self.online_translate_shortcut_linear_attaching.addWidget(
                self.online_translate_shortcut
            )
            # 在线翻译目标语言
            # 常用的 EN JA RU，更多选择参考 https://www.deepl.com/docs-api/translate-text
            self.online_translate_target_languages = SiComboBox(self)
            self.online_translate_target_languages.resize(256, 32)
            self.online_translate_target_languages.addOption("JA")
            self.online_translate_target_languages.addOption("EN")
            self.online_translate_target_languages.addOption("RU")
            self.online_translate_target_languages.addOption("FR")
            self.online_translate_target_languages.addOption("KO")
            match self.config["client"]["online_translate_target_languages"]:
                case "JA":
                    self.online_translate_target_languages.menu().setIndex(0)
                case "EN":
                    self.online_translate_target_languages.menu().setIndex(1)
                case "RU":
                    self.online_translate_target_languages.menu().setIndex(2)
                case "FR":
                    self.online_translate_target_languages.menu().setIndex(3)
                case "KO":
                    self.online_translate_target_languages.menu().setIndex(4)
                case _:
                    self.online_translate_target_languages.addOption(
                        self.config["client"]["online_translate_target_languages"]
                    )
                    self.online_translate_target_languages.menu().setIndex(-1)
            self.online_translate_target_languages_set_default = SetDefaultButton(self)
            self.online_translate_target_languages_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.online_translate_target_languages_linear_attaching.setTitle(
                "在线翻译目标语言",
                '默认值："JA"\n更多选择参考 https://www.deepl.com/docs-api/translate-text 手动修改 config.toml',
            )
            self.online_translate_target_languages_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_translate_regular")
            )
            self.online_translate_target_languages_linear_attaching.addWidget(
                self.online_translate_target_languages_set_default
            )
            self.online_translate_target_languages_linear_attaching.addWidget(
                self.online_translate_target_languages
            )
            # 控制在线翻译将光标选中的中文翻译并替换为在线翻译目标语言的快捷键
            # 如果未选中任何文字，会将剪贴板的文字翻译为目标语言并粘贴
            self.online_translate_and_replace_the_selected_text_shortcut = (
                SiLineEditWithDeletionButton(self)
            )
            self.online_translate_and_replace_the_selected_text_shortcut.resize(256, 32)
            self.online_translate_and_replace_the_selected_text_shortcut.lineEdit().setText(
                self.config["client"][
                    "online_translate_and_replace_the_selected_text_shortcut"
                ]
            )
            self.online_translate_and_replace_the_selected_text_shortcut_set_default = (
                SetDefaultButton(self)
            )
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching = SiOptionCardLinear(
                self
            )
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.setTitle(
                "将光标选中的中文翻译并替换为目标语言的快捷键",
                '默认值："ctrl + alt + ["\n未选中任何文字时\n将剪贴板的文字翻译为目标语言并粘贴',
            )
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.addWidget(
                self.online_translate_and_replace_the_selected_text_shortcut_set_default
            )
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.addWidget(
                self.online_translate_and_replace_the_selected_text_shortcut
            )

            # 设置项
            self.online_translate_container = SiDenseVContainer(self)
            self.online_translate_container.setFixedWidth(700)
            self.online_translate_container.setAdjustWidgetsSize(True)
            self.online_translate_container.addWidget(
                self.use_online_translate_function_linear_attaching
            )
            self.use_online_translate_function_changed()
            self.online_translate_container.addWidget(
                self.online_translate_shortcut_linear_attaching
            )
            self.online_translate_container.addWidget(
                self.online_translate_target_languages_linear_attaching
            )
            self.online_translate_container.addWidget(
                self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching
            )
            group.addWidget(self.online_translate_container)

        with self.titled_widgets_group as group:
            group.addTitle("使用 Everything 搜索选中文字")

            # 是否启用使用 Everything 搜索选中文字的功能
            self.use_search_selected_text_with_everything_function = SiSwitch(self)
            self.use_search_selected_text_with_everything_function.setChecked(
                self.config["client"][
                    "use_search_selected_text_with_everything_function"
                ]
            )
            self.use_search_selected_text_with_everything_function_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.use_search_selected_text_with_everything_function_linear_attaching.setTitle(
                "调用 Everything 搜索选中的文字"
            )
            self.use_search_selected_text_with_everything_function_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_search_filled")
            )
            self.use_search_selected_text_with_everything_function_linear_attaching.addWidget(
                self.use_search_selected_text_with_everything_function
            )

            # 控制使用 Everything 搜索选中文字的快捷键，默认是 "ctrl + alt + f"
            self.search_selected_text_with_everything_shortcut = (
                SiLineEditWithDeletionButton(self)
            )
            self.search_selected_text_with_everything_shortcut.resize(256, 32)
            self.search_selected_text_with_everything_shortcut.lineEdit().setText(
                self.config["client"]["search_selected_text_with_everything_shortcut"]
            )
            self.search_selected_text_with_everything_shortcut_set_default = (
                SetDefaultButton(self)
            )
            self.search_selected_text_with_everything_shortcut_linear_attaching = (
                SiOptionCardLinear(self)
            )
            self.search_selected_text_with_everything_shortcut_linear_attaching.setTitle(
                "使用 Everything 搜索选中文字的快捷键", '默认值："ctrl + alt + f"'
            )
            self.search_selected_text_with_everything_shortcut_linear_attaching.load(
                SiGlobal.siui.iconpack.get("ic_fluent_keyboard_regular")
            )
            self.search_selected_text_with_everything_shortcut_linear_attaching.addWidget(
                self.search_selected_text_with_everything_shortcut_set_default
            )
            self.search_selected_text_with_everything_shortcut_linear_attaching.addWidget(
                self.search_selected_text_with_everything_shortcut
            )

            # 设置项
            self.search__with_everything_container = SiDenseVContainer(self)
            self.search__with_everything_container.setFixedWidth(700)
            self.search__with_everything_container.setAdjustWidgetsSize(True)
            self.search__with_everything_container.addWidget(
                self.use_search_selected_text_with_everything_function_linear_attaching
            )
            self.use_search_selected_text_with_everything_function_changed()
            self.search__with_everything_container.addWidget(
                self.search_selected_text_with_everything_shortcut_linear_attaching
            )
            group.addWidget(self.search__with_everything_container)

        # 添加页脚的空白以增加美观性
        self.titled_widgets_group.addPlaceholder(64)

        # 设置控件组为页面对象
        self.setAttachment(self.titled_widgets_group)

    def on_vscode_exe_path_selected(self, path):
        self.vscode_exe_path = path
        print(f"VSCode exe path selected: {self.vscode_exe_path}")
        self.validate_vscode_exe_path()

    def hint_while_recording_at_cursor_position_changed(self):
        if self.hint_while_recording_at_cursor_position.isChecked():
            self.check_microphone_usage_by_linear_attaching.show()
        else:
            self.check_microphone_usage_by_linear_attaching.hide()

    def convert_to_traditional_chinese_main_changed(self):
        if self.convert_to_traditional_chinese_main.isChecked():
            self.convert_to_traditional_chinese_main.setText("繁")
        else:
            self.convert_to_traditional_chinese_main.setText("简")

    def paste_changed(self):
        if self.paste.isChecked():
            self.restore_clipboard_after_paste_linear_attaching.show()
        else:
            self.restore_clipboard_after_paste_linear_attaching.hide()

    def hold_mode_changed(self):
        if self.hold_mode.isChecked():
            self.suppress_linear_attaching.show()
        else:
            self.suppress_linear_attaching.hide()

    def save_audio_changed(self):
        if self.save_audio.isChecked():
            self.audio_name_len_linear_attaching.show()
            self.reduce_audio_files_linear_attaching.show()
        else:
            self.audio_name_len_linear_attaching.hide()
            self.reduce_audio_files_linear_attaching.hide()

    def use_search_selected_text_with_everything_function_changed(self):
        if self.use_search_selected_text_with_everything_function.isChecked():
            self.search_selected_text_with_everything_shortcut_linear_attaching.show()
        else:
            self.search_selected_text_with_everything_shortcut_linear_attaching.hide()

    def use_offline_translate_function_changed(self):
        if self.use_offline_translate_function.isChecked():
            self.offline_translate_port_linear_attaching.show()
            self.offline_translate_shortcut_linear_attaching.show()
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.show()
        else:
            self.offline_translate_port_linear_attaching.hide()
            self.offline_translate_shortcut_linear_attaching.hide()
            self.offline_translate_and_replace_the_selected_text_shortcut_linear_attaching.hide()

    def use_online_translate_function_changed(self):
        if self.use_online_translate_function.isChecked():
            self.online_translate_shortcut_linear_attaching.show()
            self.online_translate_target_languages_linear_attaching.show()
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.show()
        else:
            self.online_translate_shortcut_linear_attaching.hide()
            self.online_translate_target_languages_linear_attaching.hide()
            self.online_translate_and_replace_the_selected_text_shortcut_linear_attaching.hide()

    def save_config(self):
        def get_value_from_gui():
            self.config["client"]["addr"] = self.addr.line_edit.text()
            self.config["client"]["speech_recognition_port"] = str(
                self.speech_recognition_port.value()
            )
            self.config["client"]["offline_translate_port"] = str(
                self.offline_translate_port.value()
            )
            self.config["client"]["speech_recognition_shortcut"] = (
                self.speech_recognition_shortcut.line_edit.text()
            )
            self.config["client"]["use_offline_translate_function"] = (
                self.use_offline_translate_function.isChecked()
            )
            self.config["client"]["offline_translate_shortcut"] = (
                self.offline_translate_shortcut.line_edit.text()
            )
            self.config["client"][
                "offline_translate_and_replace_the_selected_text_shortcut"
            ] = self.offline_translate_and_replace_the_selected_text_shortcut.line_edit.text()
            self.config["client"]["use_online_translate_function"] = (
                self.use_online_translate_function.isChecked()
            )
            self.config["client"]["online_translate_shortcut"] = (
                self.online_translate_shortcut.line_edit.text()
            )
            self.config["client"]["online_translate_target_languages"] = (
                self.online_translate_target_languages.value_label.text()
            )
            self.config["client"][
                "online_translate_and_replace_the_selected_text_shortcut"
            ] = self.online_translate_and_replace_the_selected_text_shortcut.line_edit.text()
            self.config["client"][
                "use_search_selected_text_with_everything_function"
            ] = self.use_search_selected_text_with_everything_function.isChecked()
            self.config["client"]["search_selected_text_with_everything_shortcut"] = (
                self.search_selected_text_with_everything_shortcut.line_edit.text()
            )
            self.config["client"][
                "use_search_selected_text_with_everything_function"
            ] = self.use_search_selected_text_with_everything_function.isChecked()
            self.config["client"]["search_selected_text_with_everything_shortcut"] = (
                self.search_selected_text_with_everything_shortcut.line_edit.text()
            )
            self.config["client"]["hold_mode"] = self.hold_mode.isChecked()
            self.config["client"]["suppress"] = self.suppress.isChecked()
            self.config["client"]["restore_key"] = self.restore_key.isChecked()
            self.config["client"]["threshold"] = self.threshold.value()
            self.config["client"]["paste"] = self.paste.isChecked()
            self.config["client"]["restore_clipboard_after_paste"] = (
                self.restore_clipboard_after_paste.isChecked()
            )
            self.config["client"]["save_audio"] = self.save_audio.isChecked()
            self.config["client"]["save_markdown"] = self.save_markdown.isChecked()
            self.config["client"]["audio_name_len"] = self.audio_name_len.value()
            self.config["client"]["reduce_audio_files"] = (
                self.reduce_audio_files.isChecked()
            )
            self.config["client"]["trash_punc"] = self.trash_punc.line_edit.text()
            self.config["client"]["hot_zh"] = self.hot_zh.isChecked()
            self.config["client"]["多音字"] = self.多音字.isChecked()
            self.config["client"]["声调"] = self.声调.isChecked()
            self.config["client"]["hot_en"] = self.hot_en.isChecked()
            self.config["client"]["hot_rule"] = self.hot_rule.isChecked()
            self.config["client"]["hot_kwd"] = self.hot_kwd.isChecked()
            self.config["client"]["mic_seg_duration"] = self.mic_seg_duration.value()
            self.config["client"]["mic_seg_overlap"] = self.mic_seg_overlap.value()
            self.config["client"]["file_seg_duration"] = self.file_seg_duration.value()
            self.config["client"]["file_seg_overlap"] = self.file_seg_overlap.value()
            self.config["client"]["mute_other_audio"] = (
                self.mute_other_audio.isChecked()
            )
            self.config["client"]["pause_other_audio"] = (
                self.pause_other_audio.isChecked()
            )
            self.config["client"]["arabic_year_number"] = (
                self.arabic_year_number.isChecked()
            )
            self.config["client"]["shrink_automatically_to_tray"] = (
                self.shrink_automatically_to_tray.isChecked()
            )
            self.config["client"]["only_run_once"] = self.only_run_once.isChecked()
            self.config["client"][
                "only_enable_microphones_when_pressed_record_shortcut"
            ] = self.only_enable_microphones_when_pressed_record_shortcut.isChecked()
            self.config["client"]["vscode_exe_path"] = self.vscode_exe_path
            self.config["client"]["play_start_music"] = (
                self.play_start_music.isChecked()
            )
            self.config["client"]["start_music_path"] = (
                self.start_music_path.line_edit.text()
            )
            self.config["client"]["start_music_volume"] = str(
                self.start_music_volume.value()
            )
            self.config["client"]["play_stop_music"] = self.play_stop_music.isChecked()
            self.config["client"]["stop_music_path"] = (
                self.stop_music_path.line_edit.text()
            )
            self.config["client"]["stop_music_volume"] = str(
                self.stop_music_volume.value()
            )
            self.config["client"][
                "hint_while_recording_at_edit_position_powered_by_ahk"
            ] = self.hint_while_recording_at_edit_position_powered_by_ahk.isChecked()
            self.config["client"]["hint_while_recording_at_cursor_position"] = (
                self.hint_while_recording_at_cursor_position.isChecked()
            )
            self.config["client"]["check_microphone_usage_by"] = (
                self.check_microphone_usage_by.value_label.text()
            )
            self.config["client"]["enable_double_click_opposite_state"] = (
                self.enable_double_click_opposite_state.isChecked()
            )
            self.config["client"]["convert_to_traditional_chinese_main"] = (
                "繁" if self.convert_to_traditional_chinese_main.isChecked() else "简"
            )

        def print_config():
            from rich.console import Console
            from rich.table import Table

            from util.edit_config_gui.clearly_type import clearly_type

            console = Console()
            table = Table(title="保存 Paraformer 语音识别模型参数配置")
            table.add_column("属性名", style="cyan")
            table.add_column("类型", style="magenta")
            table.add_column("值", style="green")
            table.add_row(
                "addr",
                clearly_type(self.config["client"]["addr"]),
                str(self.config["client"]["addr"]),
            )
            table.add_row(
                "speech_recognition_port",
                clearly_type(self.config["client"]["speech_recognition_port"]),
                str(self.config["client"]["speech_recognition_port"]),
            )
            table.add_row(
                "offline_translate_port",
                clearly_type(self.config["client"]["offline_translate_port"]),
                str(self.config["client"]["offline_translate_port"]),
            )
            table.add_row(
                "speech_recognition_shortcut",
                clearly_type(self.config["client"]["speech_recognition_shortcut"]),
                str(self.config["client"]["speech_recognition_shortcut"]),
            )
            table.add_row(
                "use_offline_translate_function",
                clearly_type(self.config["client"]["use_offline_translate_function"]),
                str(self.config["client"]["use_offline_translate_function"]),
            )
            table.add_row(
                "offline_translate_shortcut",
                clearly_type(self.config["client"]["offline_translate_shortcut"]),
                str(self.config["client"]["offline_translate_shortcut"]),
            )
            table.add_row(
                "offline_translate_and_replace_the_selected_text_shortcut",
                clearly_type(
                    self.config["client"][
                        "offline_translate_and_replace_the_selected_text_shortcut"
                    ]
                ),
                str(
                    self.config["client"][
                        "offline_translate_and_replace_the_selected_text_shortcut"
                    ]
                ),
            )
            table.add_row(
                "use_online_translate_function",
                clearly_type(self.config["client"]["use_online_translate_function"]),
                str(self.config["client"]["use_online_translate_function"]),
            )
            table.add_row(
                "online_translate_shortcut",
                clearly_type(self.config["client"]["online_translate_shortcut"]),
                str(self.config["client"]["online_translate_shortcut"]),
            )
            table.add_row(
                "online_translate_target_languages",
                clearly_type(
                    self.config["client"]["online_translate_target_languages"]
                ),
                str(self.config["client"]["online_translate_target_languages"]),
            )
            table.add_row(
                "online_translate_and_replace_the_selected_text_shortcut",
                clearly_type(
                    self.config["client"][
                        "online_translate_and_replace_the_selected_text_shortcut"
                    ]
                ),
                str(
                    self.config["client"][
                        "online_translate_and_replace_the_selected_text_shortcut"
                    ]
                ),
            )
            table.add_row(
                "use_search_selected_text_with_everything_function",
                clearly_type(
                    self.config["client"][
                        "use_search_selected_text_with_everything_function"
                    ]
                ),
                str(
                    self.config["client"][
                        "use_search_selected_text_with_everything_function"
                    ]
                ),
            )
            table.add_row(
                "search_selected_text_with_everything_shortcut",
                clearly_type(
                    self.config["client"][
                        "search_selected_text_with_everything_shortcut"
                    ]
                ),
                str(
                    self.config["client"][
                        "search_selected_text_with_everything_shortcut"
                    ]
                ),
            )
            table.add_row(
                "hold_mode",
                clearly_type(self.config["client"]["hold_mode"]),
                str(self.config["client"]["hold_mode"]),
            )
            table.add_row(
                "suppress",
                clearly_type(self.config["client"]["suppress"]),
                str(self.config["client"]["suppress"]),
            )
            table.add_row(
                "restore_key",
                clearly_type(self.config["client"]["restore_key"]),
                str(self.config["client"]["restore_key"]),
            )
            table.add_row(
                "threshold",
                clearly_type(self.config["client"]["threshold"]),
                str(self.config["client"]["threshold"]),
            )
            table.add_row(
                "paste",
                clearly_type(self.config["client"]["paste"]),
                str(self.config["client"]["paste"]),
            )
            table.add_row(
                "restore_clipboard_after_paste",
                clearly_type(self.config["client"]["restore_clipboard_after_paste"]),
                str(self.config["client"]["restore_clipboard_after_paste"]),
            )
            table.add_row(
                "save_audio",
                clearly_type(self.config["client"]["save_audio"]),
                str(self.config["client"]["save_audio"]),
            )
            table.add_row(
                "save_markdown",
                clearly_type(self.config["client"]["save_markdown"]),
                str(self.config["client"]["save_markdown"]),
            )
            table.add_row(
                "audio_name_len",
                clearly_type(self.config["client"]["audio_name_len"]),
                str(self.config["client"]["audio_name_len"]),
            )
            table.add_row(
                "reduce_audio_files",
                clearly_type(self.config["client"]["reduce_audio_files"]),
                str(self.config["client"]["reduce_audio_files"]),
            )
            table.add_row(
                "trash_punc",
                clearly_type(self.config["client"]["trash_punc"]),
                str(self.config["client"]["trash_punc"]),
            )
            table.add_row(
                "hot_zh",
                clearly_type(self.config["client"]["hot_zh"]),
                str(self.config["client"]["hot_zh"]),
            )
            table.add_row(
                "多音字",
                clearly_type(self.config["client"]["多音字"]),
                str(self.config["client"]["多音字"]),
            )
            table.add_row(
                "声调",
                clearly_type(self.config["client"]["声调"]),
                str(self.config["client"]["声调"]),
            )
            table.add_row(
                "hot_en",
                clearly_type(self.config["client"]["hot_en"]),
                str(self.config["client"]["hot_en"]),
            )
            table.add_row(
                "hot_rule",
                clearly_type(self.config["client"]["hot_rule"]),
                str(self.config["client"]["hot_rule"]),
            )
            table.add_row(
                "hot_kwd",
                clearly_type(self.config["client"]["hot_kwd"]),
                str(self.config["client"]["hot_kwd"]),
            )
            table.add_row(
                "mic_seg_duration",
                clearly_type(self.config["client"]["mic_seg_duration"]),
                str(self.config["client"]["mic_seg_duration"]),
            )
            table.add_row(
                "mic_seg_overlap",
                clearly_type(self.config["client"]["mic_seg_overlap"]),
                str(self.config["client"]["mic_seg_overlap"]),
            )
            table.add_row(
                "file_seg_duration",
                clearly_type(self.config["client"]["file_seg_duration"]),
                str(self.config["client"]["file_seg_duration"]),
            )
            table.add_row(
                "file_seg_overlap",
                clearly_type(self.config["client"]["file_seg_overlap"]),
                str(self.config["client"]["file_seg_overlap"]),
            )
            table.add_row(
                "mute_other_audio",
                clearly_type(self.config["client"]["mute_other_audio"]),
                str(self.config["client"]["mute_other_audio"]),
            )
            table.add_row(
                "pause_other_audio",
                clearly_type(self.config["client"]["pause_other_audio"]),
                str(self.config["client"]["pause_other_audio"]),
            )
            table.add_row(
                "arabic_year_number",
                clearly_type(self.config["client"]["arabic_year_number"]),
                str(self.config["client"]["arabic_year_number"]),
            )
            table.add_row(
                "shrink_automatically_to_tray",
                clearly_type(self.config["client"]["shrink_automatically_to_tray"]),
                str(self.config["client"]["shrink_automatically_to_tray"]),
            )
            table.add_row(
                "only_run_once",
                clearly_type(self.config["client"]["only_run_once"]),
                str(self.config["client"]["only_run_once"]),
            )
            table.add_row(
                "only_enable_microphones_when_pressed_record_shortcut",
                clearly_type(
                    self.config["client"][
                        "only_enable_microphones_when_pressed_record_shortcut"
                    ]
                ),
                str(
                    self.config["client"][
                        "only_enable_microphones_when_pressed_record_shortcut"
                    ]
                ),
            )
            table.add_row(
                "vscode_exe_path",
                clearly_type(self.config["client"]["vscode_exe_path"]),
                str(self.config["client"]["vscode_exe_path"]),
            )
            table.add_row(
                "play_start_music",
                clearly_type(self.config["client"]["play_start_music"]),
                str(self.config["client"]["play_start_music"]),
            )
            table.add_row(
                "start_music_path",
                clearly_type(self.config["client"]["start_music_path"]),
                str(self.config["client"]["start_music_path"]),
            )
            table.add_row(
                "start_music_volume",
                clearly_type(self.config["client"]["start_music_volume"]),
                str(self.config["client"]["start_music_volume"]),
            )
            table.add_row(
                "play_stop_music",
                clearly_type(self.config["client"]["play_stop_music"]),
                str(self.config["client"]["play_stop_music"]),
            )
            table.add_row(
                "stop_music_path",
                clearly_type(self.config["client"]["stop_music_path"]),
                str(self.config["client"]["stop_music_path"]),
            )
            table.add_row(
                "stop_music_volume",
                clearly_type(self.config["client"]["stop_music_volume"]),
                str(self.config["client"]["stop_music_volume"]),
            )
            table.add_row(
                "hint_while_recording_at_edit_position_powered_by_ahk",
                clearly_type(
                    self.config["client"][
                        "hint_while_recording_at_edit_position_powered_by_ahk"
                    ]
                ),
                str(
                    self.config["client"][
                        "hint_while_recording_at_edit_position_powered_by_ahk"
                    ]
                ),
            )
            table.add_row(
                "hint_while_recording_at_cursor_position",
                clearly_type(
                    self.config["client"]["hint_while_recording_at_cursor_position"]
                ),
                str(self.config["client"]["hint_while_recording_at_cursor_position"]),
            )
            table.add_row(
                "check_microphone_usage_by",
                clearly_type(self.config["client"]["check_microphone_usage_by"]),
                str(self.config["client"]["check_microphone_usage_by"]),
            )
            table.add_row(
                "enable_double_click_opposite_state",
                clearly_type(
                    self.config["client"]["enable_double_click_opposite_state"]
                ),
                str(self.config["client"]["enable_double_click_opposite_state"]),
            )
            table.add_row(
                "convert_to_traditional_chinese_main",
                clearly_type(
                    self.config["client"]["convert_to_traditional_chinese_main"]
                ),
                str(self.config["client"]["convert_to_traditional_chinese_main"]),
            )
            console.print(table)

        from siui.core import SiGlobal

        from util.edit_config_gui.write_toml import write_toml

        try:
            self.save.clicked.emit()
            get_value_from_gui()
            print_config()
            write_toml(self.config, self.config_path)
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                "保存客户端配置成功！\n手动重启客户端以加载新配置。",
                msg_type=1,
                fold_after=2000,
            )
        except Exception as e:
            SiGlobal.siui.windows["MAIN_WINDOW"].LayerRightMessageSidebar().send(
                f"保存客户端配置失败！\n错误信息：{e}",
                msg_type=4,
            )
