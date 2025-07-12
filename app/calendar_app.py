import os
import json
from datetime import datetime, date
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem, QInputDialog,
    QTextEdit, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt

from style import light_mode

DATA_DIR = "calendar_data"
os.makedirs(DATA_DIR, exist_ok=True)


class EventManager:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir

    def get_events_for_date(self, selected_date: date):
        fname = os.path.join(self.data_dir, f"{selected_date.isoformat()}.json")
        if not os.path.exists(fname):
            return []
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_events_for_date(self, selected_date: date, events):
        fname = os.path.join(self.data_dir, f"{selected_date.isoformat()}.json")
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

    def delete_event(self, selected_date: date, index):
        events = self.get_events_for_date(selected_date)
        if 0 <= index < len(events):
            del events[index]
            self.save_events_for_date(selected_date, events)


class CalendarApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📅 MyCalendar")
        self.resize(1000, 700)
        self.manager = EventManager()
        self.current_date = date.today()

        self.setup_ui()
        self.setStyleSheet(self.light_mode_style())
        self.load_events()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.on_date_selected)

        self.event_list = QListWidget()
        self.event_list.itemDoubleClicked.connect(self.edit_event)

        self.add_btn = QPushButton("Add Event")
        self.edit_btn = QPushButton("Edit Event")
        self.delete_btn = QPushButton("Delete Event")

        self.add_btn.clicked.connect(self.add_event)
        self.edit_btn.clicked.connect(self.edit_event)
        self.delete_btn.clicked.connect(self.delete_event)

        btn_bar = QHBoxLayout()
        btn_bar.addWidget(self.add_btn)
        btn_bar.addWidget(self.edit_btn)
        btn_bar.addWidget(self.delete_btn)

        right_panel = QVBoxLayout()
        self.title = QLabel(f"Events on {self.current_date.strftime('%B %d, %Y')}")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        right_panel.addWidget(self.title)
        right_panel.addWidget(self.event_list)
        right_panel.addLayout(btn_bar)

        splitter = QSplitter(Qt.Horizontal)
        calendar_widget = QWidget()
        calendar_layout = QVBoxLayout(calendar_widget)
        calendar_layout.addWidget(QLabel("📆 Calendar"))
        calendar_layout.addWidget(self.calendar)
        splitter.addWidget(calendar_widget)

        event_widget = QWidget()
        event_widget.setLayout(right_panel)
        splitter.addWidget(event_widget)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def on_date_selected(self):
        self.current_date = self.calendar.selectedDate().toPython()
        self.title.setText(f"Events on {self.current_date.strftime('%B %d, %Y')}")
        self.load_events()

    def load_events(self):
        self.event_list.clear()
        events = self.manager.get_events_for_date(self.current_date)
        for e in events:
            self.event_list.addItem(e)

    def add_event(self):
        text, ok = QInputDialog.getMultiLineText(self, "Add Event", "Event description:")
        if ok and text.strip():
            events = self.manager.get_events_for_date(self.current_date)
            events.append(text.strip())
            self.manager.save_events_for_date(self.current_date, events)
            self.load_events()

    def edit_event(self, item=None):
        item = item or self.event_list.currentItem()
        if not item:
            return
        idx = self.event_list.row(item)
        old_text = item.text()
        new_text, ok = QInputDialog.getMultiLineText(self, "Edit Event", "Update description:", old_text)
        if ok and new_text.strip():
            events = self.manager.get_events_for_date(self.current_date)
            events[idx] = new_text.strip()
            self.manager.save_events_for_date(self.current_date, events)
            self.load_events()

    def delete_event(self):
        item = self.event_list.currentItem()
        if not item:
            return
        confirm = QMessageBox.question(self, "Delete", f"Delete event: '{item.text()}'?")
        if confirm == QMessageBox.Yes:
            idx = self.event_list.row(item)
            self.manager.delete_event(self.current_date, idx)
            self.load_events()

    def light_mode_style(self):
        return light_mode(self)