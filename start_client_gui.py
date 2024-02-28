import os
import sys
import subprocess
from queue import Queue
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QTextEdit, QSystemTrayIcon, QMenu, QPushButton, QVBoxLayout, QWidget)
from PySide6.QtGui import (QIcon, QAction)
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
        self.create_text_box()
        self.create_clear_button()  # Create clear button
        self.create_systray_icon()
        self.hide()

    def create_text_box(self):
        self.text_box_client = QTextEdit()
        self.text_box_client.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_box_client.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setCentralWidget(self.text_box_client)

    def create_clear_button(self):
        # Create a button
        self.clear_button = QPushButton("Clear Client Text", self)
        
        # Connect click event
        self.clear_button.clicked.connect(lambda: self.clear_text_box())
        
        # Create a vertical layout
        layout = QVBoxLayout()
        
        # Add text box and button to the layout
        layout.addWidget(self.text_box_client)
        layout.addWidget(self.clear_button)
        
        # Create a central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        
        # Set the central widget
        self.setCentralWidget(central_widget)

    def clear_text_box(self):
        # Clear the content of the client text box
        self.text_box_client.clear()
    
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


def start_client_gui():
    if Config.Only_run_once and check_process('pythonw_CapsWriter_Client.exe'):
            raise Exception("已经有一个客户端在运行了！（用户配置了 只允许运行一次，禁止多开；而且检测到 pythonw_CapsWriter_Client.exe 进程已在运行。如果你确定需要启动多个客户端同时运行，请先修改 config.py  class ClientConfig:  Only_run_once = False 。）")
    subprocess.Popen(['hint_while_recording.exe'], creationflags=subprocess.CREATE_NO_WINDOW)
    app = QApplication([])
    apply_stylesheet(app, theme='dark_teal.xml')
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
