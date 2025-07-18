import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QFrame, QToolButton, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from chat_app import MyIQWindow
from calendar_app import CalendarApp
from notebook import NotebookWidget
# from widgets.mindmap_widget import MindMapWidget


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyIQ")
        self.setMinimumSize(1100, 700)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QHBoxLayout()
        self.hamburger_btn = QToolButton()
        self.hamburger_btn.setText("☰")
        self.hamburger_btn.setStyleSheet("font-size: 22px; border: none;")
        self.hamburger_btn.clicked.connect(self.toggle_sidebar)
        top_bar.addWidget(self.hamburger_btn)
        top_bar.addStretch()

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = QFrame()
        self.sidebar.setMinimumWidth(220)
        self.sidebar.setStyleSheet("background-color: #F7F7F8;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setSpacing(10)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 10)

        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                text-align: left;
                padding: 10px 15px;
                font-size: 16px;
                color: #333;
            }
            QPushButton:hover {
                background-color: #eaeaea;
            }
            QPushButton:checked {
                background-color: #dcdcdc;
                font-weight: bold;
            }
        """

        self.chat_btn = QPushButton("🧠  Intelligence")
        self.cal_btn = QPushButton("📆  Timeline")
        self.notes_btn = QPushButton("📝  Notebook")

        for btn in [self.chat_btn, self.cal_btn, self.notes_btn]:
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()

        self.stack = QStackedWidget()
        self.chat_widget = MyIQWindow()
        self.calendar_widget = CalendarApp()
        self.notes_widget = NotebookWidget()

        self.stack.addWidget(self.chat_widget)
        self.stack.addWidget(self.calendar_widget)
        self.stack.addWidget(self.notes_widget)

        self.chat_btn.clicked.connect(lambda: self.switch_app(0))
        self.cal_btn.clicked.connect(lambda: self.switch_app(1))
        self.notes_btn.clicked.connect(lambda: self.switch_app(2))

        self.chat_btn.setChecked(True)
        self.switch_app(0)

        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(self.stack, 1)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(main_widget)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def switch_app(self, index):
        self.stack.setCurrentIndex(index)
        for btn in [self.chat_btn, self.cal_btn, self.notes_btn]:
            btn.setChecked(False)
        [self.chat_btn, self.cal_btn, self.notes_btn][index].setChecked(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())
