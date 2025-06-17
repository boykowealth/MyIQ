import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton,
    QFileDialog, QVBoxLayout, QWidget, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, QEvent, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QFontMetrics
from chat_handler import get_llm_response
from file_parser import parse_file
from voice_trigger import start_voice_listener


class ChatBubble(QWidget):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.text = text
        self.is_user = is_user
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.margin = 15
        self.padding = 10
        self.max_width = 400
        self.setMinimumHeight(20)
        self.setContentsMargins(0, 0, 0, 0)

        fm = QFontMetrics(self.font())
        rect = fm.boundingRect(0, 0, self.max_width, 1000, Qt.TextWordWrap, self.text)
        self.text_rect = rect.adjusted(-self.padding, -self.padding, self.padding, self.padding)
        self.setMinimumHeight(self.text_rect.height() + self.margin)

    def sizeHint(self):
        return QSize(self.text_rect.width() + self.margin * 2, self.text_rect.height() + self.margin * 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(self.margin, self.margin, -self.margin, -self.margin)

        bubble_color = QColor("#105384") if self.is_user else QColor("#ffffff")
        border_color = QColor("#08324f") if self.is_user else QColor("#bbb")

        if self.is_user:
            rect.moveLeft(self.width() - rect.width() - self.margin)

        painter.setBrush(bubble_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(rect, 10, 10)

        text_rect = rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        painter.setPen(Qt.white if self.is_user else Qt.black)
        painter.drawText(text_rect, Qt.TextWordWrap, self.text)


class ChatItemWidget(QWidget):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.is_user = is_user

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        icon_label = QLabel()
        icon_size = 24
        icon_label.setFixedSize(icon_size, icon_size)

        if is_user:
            icon = QIcon("icons/user_icon.png")
            name = "You"
        else:
            icon = QIcon("icons/MyIQICon.png")
            name = "MyIQ"

        pixmap = icon.pixmap(icon_size, icon_size)
        icon_label.setPixmap(pixmap)

        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; color: #105384;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        layout.addWidget(header)

        self.bubble = ChatBubble(text, is_user)
        layout.addWidget(self.bubble)


class LLMThread(QThread):
    response_ready = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        response = get_llm_response(self.prompt)
        self.response_ready.emit(response)


class MyIQWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyIQ")
        self.resize(800, 600)

        self.attachments = []

        self.chat_area = QListWidget()
        self.chat_area.setStyleSheet("background-color: #ddd5c2; border: none;")
        self.chat_area.setSpacing(10)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.upload_button = QPushButton()
        self.upload_button.setIcon(QIcon("icons/paperclip.png"))
        self.upload_button.setFixedSize(32, 32)
        self.upload_button.setToolTip("Upload File")
        self.upload_button.setStyleSheet("border:none;")

        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(45)
        self.input_box.setAcceptRichText(False)
        self.input_box.installEventFilter(self)

        self.send_button = QPushButton("Send")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.upload_button)
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("MyIQ Chat"))
        layout.addWidget(self.chat_area)
        layout.addLayout(input_layout)

        button_layout = QHBoxLayout()
        self.voice_button = QPushButton("🎙️ Voice On")
        button_layout.addWidget(self.voice_button)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.send_button.clicked.connect(self.send_message)
        self.upload_button.clicked.connect(self.upload_file)
        self.voice_button.clicked.connect(start_voice_listener)

        self.setStyleSheet(self.bubbly_style())

    def bubbly_style(self):
        return """
        QMainWindow {
            background-color: #ddd5c2;
        }

        QLabel {
            font-size: 18px;
            font-weight: bold;
            color: #105384;
            padding: 6px;
        }

        QTextEdit {
            background-color: #ffffff;
            border: 2px solid #105384;
            border-radius: 12px;
            padding: 10px;
            font-size: 14px;
            color: #333;
        }

        QPushButton {
            background-color: #105384;
            border-radius: 14px;
            padding: 8px 18px;
            font-size: 14px;
            color: white;
        }

        QPushButton:hover {
            background-color: #0d456d;
        }

        QPushButton:pressed {
            background-color: #08324f;
        }
        """

    def eventFilter(self, obj, event):
        if obj == self.input_box:
            if event.type() == QEvent.KeyPress:
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if event.modifiers() == Qt.ShiftModifier:
                        return False
                    else:
                        self.send_message()
                        return True
        return super().eventFilter(obj, event)

    def add_chat_bubble(self, text, is_user=False):
        widget = ChatItemWidget(text, is_user)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.chat_area.addItem(item)
        self.chat_area.setItemWidget(item, widget)
        self.chat_area.scrollToBottom()

    def send_message(self):
        user_input = self.input_box.toPlainText().strip()
        if not user_input and not self.attachments:
            return

        user_message = user_input
        if self.attachments:
            attach_text = "\n".join(f"📎 {path}" for path, _ in self.attachments)
            user_message += "\n" + attach_text

        self.add_chat_bubble(user_message, is_user=True)
        self.input_box.clear()
        self.attachments.clear()

        prompt = user_input
        if self.attachments:
            for _, content in self.attachments:
                prompt += f"\n\nAttached Content:\n{content}"

        self.thread = LLMThread(prompt)
        self.thread.response_ready.connect(self.on_llm_response)
        self.thread.start()

    def on_llm_response(self, response):
        self.add_chat_bubble(response, is_user=False)

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            content = parse_file(file_path)
            self.attachments.append((file_path, content))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyIQWindow()
    window.show()
    sys.exit(app.exec())
