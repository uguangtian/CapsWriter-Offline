import os
import sys
import subprocess
from queue import Queue
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QSystemTrayIcon, QMenu, QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout, QWidget, QLabel)
from PySide6.QtGui import (QIcon, QAction, QWheelEvent)
from PySide6.QtCore import (Qt, QTimer)
from qt_material import apply_stylesheet
from config import ClientConfig as Config
from util.check_process import check_process

def check_process(name):
    # 使用wmic命令查找进程
    command = ['wmic', 'process', 'get', 'name']
    # 执行命令并捕获输出
    output = subprocess.check_output(command).decode('utf-8', errors='replace')

    # 检查进程名称是否在输出中
    return name in output
class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.output_queue_client = Queue()
        self.start_script()

    def init_ui(self):
        self.resize(425, 425)
        self.setWindowTitle('CapsWriter-Offline-Client')
        self.setWindowIcon(QIcon("assets/client-icon.ico"))
        self.setWindowOpacity(0.9)

        self.create_text_box()
        self.create_monitor_checkbox() # Create monitor checkbox
        self.create_stay_on_top_checkbox()
        self.create_wordcount_label()
        self.create_clear_button()  # Create clear button
        self.create_systray_icon()


        # Create a vertical layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)  # 设置控件间距为0像素
        self.layout.setContentsMargins(0, 0, 0, 0)  # 设置左、上、右、下的边距为0像素
        self.layout2 = QHBoxLayout()
        self.layout2.setSpacing(0)  # 设置控件间距为0像素
        self.layout2.setContentsMargins(0, 0, 0, 0)  # 设置左、上、右、下的边距为0像素
        
        # Add text box and button to the layout
        self.layout.addWidget(self.text_box_client)
        self.layout2.addWidget(self.monitor_checkbox)
        self.layout2.addWidget(self.stay_on_top_checkbox)
        self.layout2.addWidget(self.text_box_wordCountLabel)
        self.layout2.addWidget(self.clear_button)
        self.layout.addLayout(self.layout2)


        # Create a central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        # Set the central widget
        self.setCentralWidget(central_widget)

    def create_text_box(self):
        self.text_box_client = QTextEdit()
        self.text_box_client.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_box_client.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def create_monitor_checkbox(self):
        # 创建一个QCheckBox控件
        self.monitor_checkbox = QCheckBox("Display Output")
        self.monitor_checkbox.setToolTip("Monitor Client Output / Use As Notepad")
        # 当状态改变时，调用self.on_monitor_toggled函数
        self.monitor_checkbox.stateChanged.connect(self.on_monitor_toggled)
        # 设置默认状态
        self.monitor_checkbox.setChecked(True)

    def create_stay_on_top_checkbox(self):
        self.stay_on_top_checkbox = QCheckBox('Stay On Top')
        self.stay_on_top_checkbox.stateChanged.connect(self.window_stay_on_top_toggled)
        self.stay_on_top_checkbox.setChecked(True)

    def create_wordcount_label(self):
        self.text_box_wordCountLabel = QLabel("0", self)
        self.text_box_wordCountLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.text_box_client.textChanged.connect(self.update_word_count_toggled)

    def create_clear_button(self):
        # Create a button
        self.clear_button = QPushButton("Clear", self)
        # Connect click event
        self.clear_button.clicked.connect(lambda: self.clear_text_box())

    def create_systray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/client-icon.ico"))
        edit_hot_en_action = QAction("Edit hot-en.txt", self)
        edit_hot_rule_action = QAction("Edit hot-rule.txt", self)
        edit_hot_zh_action = QAction("Edit hot-zh.txt", self)
        edit_keyword_action = QAction("Edit keywords.txt", self)
        github_website_action = QAction("🌐 GitHub Website", self)
        show_action = QAction("🪟 Show", self)
        quit_action = QAction("❌ Quit", self)

        edit_hot_en_action.triggered.connect(self.edit_hot_en)
        edit_hot_rule_action.triggered.connect(self.edit_hot_rule)
        edit_hot_zh_action.triggered.connect(self.edit_hot_zh)
        edit_keyword_action.triggered.connect(self.edit_keyword)
        github_website_action.triggered.connect(self.open_github_website)
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        tray_menu = QMenu()
        edit_menu = QMenu("📝 Edit Hot Rules", tray_menu)

        edit_menu.addAction(edit_hot_en_action)
        edit_menu.addAction(edit_hot_rule_action)
        edit_menu.addAction(edit_hot_zh_action)
        edit_menu.addAction(edit_keyword_action)

        tray_menu.addMenu(edit_menu)
        tray_menu.addAction(github_website_action)
        tray_menu.addSeparator()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()


    def clear_text_box(self):
        # Clear the content of the client text box
        self.text_box_client.clear()
    

    def on_monitor_toggled(self, state):
        # 检查复选框的选中状态
        if state == 2:  # 2 表示选中状态
            self.update_timer.start(100)
        else:
            self.update_timer.stop()

    def window_stay_on_top_toggled(self):
        # 切换窗口置顶状态
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.show()  # 重新显示窗口以应用更改

    def update_word_count_toggled(self):
        self.text_box_wordCountLabel.setText(f"{len(self.text_box_client.toPlainText())}")

    def edit_hot_en(self):
        os.startfile('hot-en.txt')
    def edit_hot_rule(self):
        os.startfile('hot-rule.txt')
    def edit_hot_zh(self):
        os.startfile('hot-zh.txt')
    def edit_keyword(self):
        os.startfile('keywords.txt')

    def open_github_website(self):
        os.system(f'start https://github.com/H1DDENADM1N/CapsWriter-Offline')
    def closeEvent(self, event):
        # Minimize to system tray instead of closing the window when the user clicks the close button
        self.hide()  # Hide the window
        event.ignore()  # Ignore the close event
    
    def quit_app(self):
        # Terminate core_client.py process
        if hasattr(self, 'core_client_process') and self.core_client_process:
            self.core_client_process.terminate()
            self.core_client_process.kill()
        
        # Hide the system tray icon
        self.tray_icon.setVisible(False)
        
        # Quit the application
        QApplication.quit()

        # TODO: Quit models The above method can not completely exit the model, rename pythonw.exe to pythonw_CapsWriter.exe and taskkill. It's working but not the best way.
        proc = subprocess.Popen('taskkill /IM pythonw_CapsWriter_Client.exe /IM hint_while_recording.exe /IM deeplx_windows_amd64.exe /F', creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)


    def on_tray_icon_activated(self, reason):
        # Called when the system tray icon is activated
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()  # Show the main window

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide() # Press ESC to hide main window

    def start_script(self):
        # Start core_client.py and redirect output to the client queue

        # While Debug error    for line in iter(out.readline, ''):
        # Use this line to replace the original code
        # self.core_client_process = subprocess.Popen(['.\\runtime\\pythonw_CapsWriter_Client.exe', 'core_client.py'], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        
        self.core_client_process = subprocess.Popen(['.\\runtime\\pythonw_CapsWriter_Client.exe', 'core_client.py'], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        threading.Thread(target=self.enqueue_output, args=(self.core_client_process.stdout, self.output_queue_client), daemon=True).start()

        # Update text box
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_text_box)
        self.update_timer.start(100)


    def enqueue_output(self, out, queue):
        for line in iter(out.readline, ''): # While Debug error     UnicodeDecodeError: 'gbk' codec can't decode byte 0x80 in position 2: illegal multibyte sequence
                                            # Change                self.core_client_process = subprocess.Popen(['.\\runtime\\pythonw_CapsWriter_Client.exe', 'core_client.py'], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            line = line.strip()
            queue.put(line)

    def update_text_box(self):
        # Update client text box
        while not self.output_queue_client.empty():
            line = self.output_queue_client.get()
            self.text_box_client.append(line)


    def enterEvent(self, event):
        super().enterEvent(event)
        for i in range(self.layout2.count()):
            widget = self.layout2.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        for i in range(self.layout2.count()):
            widget = self.layout2.itemAt(i).widget()
            if widget is not None:
                widget.setVisible(False)

    def wheelEvent(self, event: QWheelEvent):
        # 设置初始缩放因子
        self.scale_factor = 1.0
        # 设置缩放因子的最小和最大值
        self.min_scale = 0.5
        self.max_scale = 2.0
        # 检测Ctrl键是否被按下
        if event.modifiers() == Qt.ControlModifier:
            # 计算缩放因子
            # print(event.angleDelta().y())
            if event.angleDelta().y() > 0:
                self.scale_factor *= 1.1  # 放大
            elif event.angleDelta().y() < 0:
                self.scale_factor *= 0.9  # 缩小
            # 限制缩放因子的范围
            self.scale_factor = max(self.min_scale, min(self.max_scale, self.scale_factor))
            # 应用缩放因子到所有控件
            self.apply_scale_factor()
        else:
            super().wheelEvent(event)

    def apply_scale_factor(self):
        # 应用缩放因子
        for widget in [self.text_box_client]:
            # 检查字体大小是否已设置，如果没有设置，则使用一个默认值
            current_font = widget.font()
            if current_font.pointSizeF() < 9:
                current_font.setPointSizeF(9)  # 设置一个默认字体大小
            current_font.setPointSizeF(current_font.pointSizeF() * self.scale_factor)
            widget.setFont(current_font)


def start_client_gui():
    if Config.Only_run_once and check_process('pythonw_CapsWriter_Client.exe'):
            raise Exception("已经有一个客户端在运行了！（用户配置了 只允许运行一次，禁止多开；而且检测到 pythonw_CapsWriter_Client.exe 进程已在运行。如果你确定需要启动多个客户端同时运行，请先修改 config.py  class ClientConfig:  Only_run_once = False 。）")
    if not check_process('hint_while_recording.exe'):
        subprocess.Popen(['hint_while_recording.exe'], creationflags=subprocess.CREATE_NO_WINDOW)
    app = QApplication([])
    apply_stylesheet(app, theme='dark_teal.xml', css_file='util\\client_gui_theme_custom.css')
    gui = GUI()
    if not Config.Shrink_automatically_to_Tray:
        gui.show()
    sys.exit(app.exec()) 




if __name__ == '__main__':
    if sys.argv[1:]:
        # 如果参数传入文件，那就转录文件
        CapsWriter_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(CapsWriter_path, 'core_client.py')
        python_exe_path = os.path.join(CapsWriter_path, 'runtime\\python.exe')
        args = [arg for arg in sys.argv[1:]]
        subprocess.run([python_exe_path, script_path] + args)
    else:
        # GUI
        start_client_gui()
