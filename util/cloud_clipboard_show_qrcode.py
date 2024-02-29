from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap, QImage
import qrcode
from io import BytesIO
import sys
import webbrowser
from PySide6.QtCore import Qt
from util.cloud_clipboard import CloudClipboard


class QRCODE(QWidget):
    def __init__(self, text, qr_data):
        super().__init__()

        self.setWindowTitle("Text and QR Code Display")
        layout = QVBoxLayout(self)

        # Create a label for the text
        text_label = QLabel(text)
        text_label.setOpenExternalLinks(True)
        text_label.setTextFormat(Qt.TextFormat.RichText)
        text_label.setText(f"<a href='{text}'>{text}</a>")
        layout.addWidget(text_label)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create an image from the QR Code instance
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer)
        qimg = QImage.fromData(img_buffer.getvalue())

        # Create a pixmap and a label for the QR code
        qr_pixmap = QPixmap.fromImage(qimg)
        qr_label = QLabel()
        qr_label.setPixmap(qr_pixmap)
        qr_label.mousePressEvent = self.open_url  # Connect the event
        layout.addWidget(qr_label)

    def open_url(self, event):
        webbrowser.open(self.qr_data)  # Use the instance variable

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()  # Close the window on ESC press


def CloudClipboardShowQRCode(text):
    # https://cv.j20.cc/  限制 *请输入5~1000个字符
    text = text.replace('\n', ' ').replace('\t', ' ')
    if len(text) < 5:
        text = text.ljust(5, ".")
    if len(text) > 1000:
        text = text[:999]
    url = CloudClipboard().post_data(text)
    qrcode = QRCODE(url, url)
    qrcode.show()

if __name__ == "__main__":
    app = QApplication([])
    text = 'Hey'
    print(len(text))
    CloudClipboardShowQRCode(text)
    sys.exit(app.exec())

