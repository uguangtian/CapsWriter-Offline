import sys
import win32api
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from PySide6.QtCore import QTimer, QPoint, Qt, QRect, QSize
from PySide6.QtGui import QPalette, QColor

class Cursor_Position(QMainWindow):
    def __init__(self):
        super().__init__()

        self.label = QLabel("", self)
        self.label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        palette = self.label.palette()
        palette.setColor(QPalette.Window, QColor("#212121"))  # 设置背景颜色
        palette.setColor(QPalette.WindowText, QColor("#00B294"))  # 设置文本颜色
        self.label.setPalette(palette)

        # 创建一个定时器来定期更新鼠标位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_tooltip_position)
        self.timer.start(100)  # 每100毫秒更新一次

    def update_tooltip_position(self):
        # 使用pywin32获取全局鼠标位置
        x, y = win32api.GetCursorPos()
        # 更新标签的位置和文本
        self.label.move(x+20,y+20)
        self.label.setText(f"X: {x}, Y: {y}")
        self.label.setVisible(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Cursor_Position()
    window.setWindowTitle("Cursor Position Follower")
    # 设置窗口位置和大小，这里设置为屏幕中心
    screen = app.primaryScreen()
    available_geo = screen.availableGeometry()
    # 计算窗口的左上角坐标
    top_left = available_geo.center() - QPoint(100, 50)
    # 创建QRect对象
    window_rect = QRect(top_left, QSize(200, 200))
    window.setGeometry(window_rect)
    window.show()
    sys.exit(app.exec())
