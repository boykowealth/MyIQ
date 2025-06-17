# main.py
import sys
import json
import os
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QPushButton,
    QFileDialog, QVBoxLayout, QWidget, QLabel, QHBoxLayout,
    QListWidget, QListWidgetItem, QSizePolicy, QSplitter,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QInputDialog,
    QMenu, QHeaderView
)
from PySide6.QtCore import Qt, QEvent, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QPainter, QColor, QFontMetrics, QAction
from chat_handler import get_llm_response
from file_parser import parse_file
from voice_trigger import start_voice_listener


class ChatSession:
    def __init__(self, session_id=None, title="New Chat"):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.title = title
        self.messages = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, text, is_user=False, attachments=None):
        message = {
            'text': text,
            'is_user': is_user,
            'timestamp': datetime.now().isoformat(),
            'attachments': attachments or []
        }
        self.messages.append(message)
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            'session_id': self.session_id,
            'title': self.title,
            'messages': self.messages,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(data['session_id'], data['title'])
        session.messages = data['messages']
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.updated_at = datetime.fromisoformat(data['updated_at'])
        return session


class ChatHistoryManager:
    def __init__(self, data_dir="chat_history"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.sessions_file = os.path.join(data_dir, "sessions.json")

    def save_session(self, session):
        sessions = self.load_all_sessions()
        sessions[session.session_id] = session.to_dict()
        
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)

    def load_session(self, session_id):
        sessions = self.load_all_sessions()
        if session_id in sessions:
            return ChatSession.from_dict(sessions[session_id])
        return None

    def load_all_sessions(self):
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def delete_session(self, session_id):
        sessions = self.load_all_sessions()
        if session_id in sessions:
            del sessions[session_id]
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)

    def get_session_list(self):
        sessions = self.load_all_sessions()
        session_list = []
        for session_data in sessions.values():
            session_list.append({
                'id': session_data['session_id'],
                'title': session_data['title'],
                'updated_at': session_data['updated_at']
            })
        # Sort by updated_at descending
        session_list.sort(key=lambda x: x['updated_at'], reverse=True)
        return session_list


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

        bubble_color = QColor("#E6F0FF") if self.is_user else QColor("#FFFFFF")
        border_color = QColor("#105384") if self.is_user else QColor("#DADCE0")

        if self.is_user:
            rect.moveLeft(self.width() - rect.width() - self.margin)

        painter.setBrush(bubble_color)
        painter.setPen(border_color)
        painter.drawRoundedRect(rect, 10, 10)

        text_rect = rect.adjusted(self.padding, self.padding, -self.padding, -self.padding)
        painter.setPen(QColor("#202123"))
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
            icon = QIcon("icons/MyIQIcon.png")
            name = "MyIQ"

        pixmap = icon.pixmap(icon_size, icon_size)
        icon_label.setPixmap(pixmap)

        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; color: #555;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(name_label)
        header_layout.addStretch()

        layout.addWidget(header)

        self.bubble = ChatBubble(text, is_user)
        layout.addWidget(self.bubble)


class LLMThread(QThread):
    response_ready = Signal(str)

    def __init__(self, prompt, conversation_history=None):
        super().__init__()
        self.prompt = prompt
        self.conversation_history = conversation_history or []

    def run(self):
        # Include conversation history in the prompt for context
        full_prompt = self.prompt
        if self.conversation_history:
            history_text = "\n\nConversation History:\n"
            for msg in self.conversation_history[-10:]:  # Last 10 messages for context
                role = "User" if msg['is_user'] else "Assistant"
                history_text += f"{role}: {msg['text']}\n"
            full_prompt = history_text + "\nCurrent message: " + self.prompt
        
        response = get_llm_response(full_prompt)
        self.response_ready.emit(response)


class MyIQWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyIQ - Chat Assistant")
        self.resize(1200, 800)

        self.history_manager = ChatHistoryManager()
        self.current_session = None
        self.attachments = []

        self.setup_ui()
        self.setup_connections()
        self.load_session_list()
        self.create_new_session()

    def setup_ui(self):
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Session list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Session controls
        session_controls = QHBoxLayout()
        self.new_chat_button = QPushButton("New Chat")
        self.delete_chat_button = QPushButton("Delete")
        session_controls.addWidget(self.new_chat_button)
        session_controls.addWidget(self.delete_chat_button)
        
        # Session list
        self.session_list = QTreeWidget()
        self.session_list.setHeaderLabels(["Chat Sessions"])
        self.session_list.header().setSectionResizeMode(QHeaderView.Stretch)
        self.session_list.setRootIsDecorated(False)
        self.session_list.setContextMenuPolicy(Qt.CustomContextMenu)
        
        left_layout.addLayout(session_controls)
        left_layout.addWidget(self.session_list)
        
        # Right panel - Chat area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Chat title
        self.chat_title_label = QLabel("New Chat")
        self.chat_title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        
        # Chat area
        self.chat_area = QListWidget()
        self.chat_area.setStyleSheet("background-color: #F7F7F8; border: none;")
        self.chat_area.setSpacing(10)
        self.chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        
        # File attachments display
        self.attachments_label = QLabel("")
        self.attachments_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        
        # Input controls
        controls_layout = QHBoxLayout()
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

        controls_layout.addWidget(self.upload_button)
        controls_layout.addWidget(self.input_box)
        controls_layout.addWidget(self.send_button)

        # Voice button
        voice_layout = QHBoxLayout()
        self.voice_button = QPushButton("🎙️ Voice On")
        voice_layout.addWidget(self.voice_button)
        
        input_layout.addWidget(self.attachments_label)
        input_layout.addLayout(controls_layout)
        input_layout.addLayout(voice_layout)
        
        right_layout.addWidget(self.chat_title_label)
        right_layout.addWidget(self.chat_area)
        right_layout.addWidget(input_widget)
        
        # Add panels to splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([300, 900])
        
        self.setCentralWidget(main_splitter)
        self.setStyleSheet(self.light_mode_style())

    def setup_connections(self):
        self.send_button.clicked.connect(self.send_message)
        self.upload_button.clicked.connect(self.upload_file)
        self.voice_button.clicked.connect(start_voice_listener)
        self.new_chat_button.clicked.connect(self.create_new_session)
        self.delete_chat_button.clicked.connect(self.delete_current_session)
        self.session_list.itemClicked.connect(self.load_selected_session)
        self.session_list.customContextMenuRequested.connect(self.show_context_menu)

    def light_mode_style(self):
        return """
        QMainWindow {
            background-color: #F7F7F8;
        }

        QLabel {
            font-size: 14px;
            color: #202123;
            padding: 6px;
        }

        QTextEdit {
            background-color: #FFFFFF;
            border: 2px solid #DADCE0;
            border-radius: 12px;
            padding: 10px;
            font-size: 14px;
            color: #202123;
        }

        QPushButton {
            background-color: #105384;
            border-radius: 14px;
            padding: 8px 18px;
            font-size: 14px;
            color: #FFFFFF;
        }

        QPushButton:hover {
            background-color: #13b28f;
        }

        QPushButton:pressed {
            background-color: #0e8f6c;
        }

        QListWidget {
            background-color: #F7F7F8;
            border: none;
        }
        
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #DADCE0;
            border-radius: 8px;
        }
        
        QTreeWidget::item {
            padding: 8px;
            border-bottom: 1px solid #F0F0F0;
        }
        
        QTreeWidget::item:selected {
            background-color: #E6F0FF;
            color: #105384;
        }
        """

    def eventFilter(self, obj, event):
        if obj == self.input_box and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() == Qt.ShiftModifier:
                    return False
                else:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)

    def create_new_session(self):
        self.current_session = ChatSession()
        self.current_session.title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.chat_title_label.setText(self.current_session.title)
        self.clear_chat_area()
        self.load_session_list()
        self.select_current_session()

    def delete_current_session(self):
        if not self.current_session:
            return
            
        reply = QMessageBox.question(
            self, 'Delete Chat', 
            'Are you sure you want to delete this chat session?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.delete_session(self.current_session.session_id)
            self.load_session_list()
            self.create_new_session()

    def load_selected_session(self, item):
        session_id = item.data(0, Qt.UserRole)
        if session_id:
            session = self.history_manager.load_session(session_id)
            if session:
                self.current_session = session
                self.chat_title_label.setText(session.title)
                self.load_chat_history()

    def select_current_session(self):
        if not self.current_session:
            return
            
        for i in range(self.session_list.topLevelItemCount()):
            item = self.session_list.topLevelItem(i)
            if item.data(0, Qt.UserRole) == self.current_session.session_id:
                self.session_list.setCurrentItem(item)
                break

    def load_session_list(self):
        self.session_list.clear()
        sessions = self.history_manager.get_session_list()
        
        for session_info in sessions:
            item = QTreeWidgetItem()
            item.setText(0, session_info['title'])
            item.setData(0, Qt.UserRole, session_info['id'])
            self.session_list.addTopLevelItem(item)

    def load_chat_history(self):
        self.clear_chat_area()
        if self.current_session:
            for message in self.current_session.messages:
                self.add_chat_bubble(message['text'], message['is_user'])

    def clear_chat_area(self):
        self.chat_area.clear()

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
            attach_text = "\n".join(f"📎 {os.path.basename(path)}" for path, _ in self.attachments)
            user_message += "\n" + attach_text

        self.add_chat_bubble(user_message, is_user=True)

        # Save user message to session
        if self.current_session:
            attachment_info = [(path, content) for path, content in self.attachments]
            self.current_session.add_message(user_message, is_user=True, attachments=attachment_info)

        self.input_box.clear()
        self.attachments.clear()
        self.update_attachments_display()

        # Prepare prompt with attachments
        prompt = user_input
        if self.attachments:
            for _, content in self.attachments:
                prompt += f"\n\nAttached Content:\n{content}"

        # Include conversation history for context
        history = self.current_session.messages if self.current_session else []
        self.thread = LLMThread(prompt, history)
        self.thread.response_ready.connect(self.on_llm_response)
        self.thread.start()

    def on_llm_response(self, response):
        self.add_chat_bubble(response, is_user=False)
        
        # Save assistant response to session
        if self.current_session:
            self.current_session.add_message(response, is_user=False)
            self.history_manager.save_session(self.current_session)
            self.load_session_list()
            self.select_current_session()

    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path:
            content = parse_file(file_path)
            self.attachments.append((file_path, content))
            self.update_attachments_display()

    def update_attachments_display(self):
        if self.attachments:
            files = [os.path.basename(path) for path, _ in self.attachments]
            self.attachments_label.setText(f"📎 Attached: {', '.join(files)}")
        else:
            self.attachments_label.setText("")

    def show_context_menu(self, position):
        item = self.session_list.itemAt(position)
        if item:
            menu = QMenu()
            
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_session(item))
            menu.addAction(rename_action)
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_session(item))
            menu.addAction(delete_action)
            
            menu.exec_(self.session_list.mapToGlobal(position))

    def rename_session(self, item):
        session_id = item.data(0, Qt.UserRole)
        current_title = item.text(0)
        
        new_title, ok = QInputDialog.getText(
            self, 'Rename Chat', 'Enter new title:', text=current_title
        )
        
        if ok and new_title.strip():
            session = self.history_manager.load_session(session_id)
            if session:
                session.title = new_title.strip()
                self.history_manager.save_session(session)
                self.load_session_list()
                if self.current_session and self.current_session.session_id == session_id:
                    self.current_session.title = new_title.strip()
                    self.chat_title_label.setText(new_title.strip())

    def delete_session(self, item):
        session_id = item.data(0, Qt.UserRole)
        session_title = item.text(0)
        
        reply = QMessageBox.question(
            self, 'Delete Chat', 
            f'Are you sure you want to delete "{session_title}"?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.delete_session(session_id)
            self.load_session_list()
            if self.current_session and self.current_session.session_id == session_id:
                self.create_new_session()
