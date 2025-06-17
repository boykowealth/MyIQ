# collapsible_section.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QSizePolicy
from PySide6.QtCore import Qt, Property, QParallelAnimationGroup, QPropertyAnimation


class CollapsibleSection(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                font-weight: bold;
                text-align: left;
                padding: 8px;
            }
            QPushButton:checked {
                background-color: #D0D0D0;
            }
        """)

        self.content_area = QWidget()
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_area.setLayout(self.content_layout)

        self.toggle_button.toggled.connect(self.toggle)

        self.anim = QParallelAnimationGroup(self)

        self.content_animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.content_animation.setDuration(200)
        self.content_animation.setStartValue(0)
        self.content_animation.setEndValue(0)

        self.anim.addAnimation(self.content_animation)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def toggle(self, checked):
        if checked:
            self.content_animation.setDirection(QPropertyAnimation.Forward)
        else:
            self.content_animation.setDirection(QPropertyAnimation.Backward)

        self.content_animation.setEndValue(self.content_layout.sizeHint().height())
        self.anim.start()

    def addWidget(self, widget):
        self.content_layout.addWidget(widget)