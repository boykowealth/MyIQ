from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel,
    QHBoxLayout, QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QSplitter
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt
import markdown2
from datetime import datetime
import os
import json

class NotebookSession:
    def __init__(self, session_id=None, title="Untitled", content=""):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.title = title
        self.content = content
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(data['session_id'], data['title'], data['content'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.updated_at = datetime.fromisoformat(data['updated_at'])
        return session
    
class NotebookManager:
    def __init__(self, data_dir="notebook_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def get_all_sessions(self):
        notebooks = []
        for fname in os.listdir(self.data_dir):
            if fname.endswith(".json"):
                path = os.path.join(self.data_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    notebooks.append(NotebookSession.from_dict(data))
        notebooks.sort(key=lambda x: x.updated_at, reverse=True)
        return notebooks

    def save_session(self, session: NotebookSession):
        session.updated_at = datetime.now()
        path = os.path.join(self.data_dir, f"{session.session_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def delete_session(self, session_id):
        path = os.path.join(self.data_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)


class NotebookWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = NotebookManager()
        self.current_session = None

        # UI
        layout = QHBoxLayout(self)
        self.list = QListWidget()
        self.editor = QTextEdit()
        self.viewer = QWebEngineView()

        button_bar = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.save_btn = QPushButton("Save")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.render_btn = QPushButton("Render")
        button_bar.addWidget(self.new_btn)
        button_bar.addWidget(self.save_btn)
        button_bar.addWidget(self.rename_btn)
        button_bar.addWidget(self.delete_btn)
        button_bar.addStretch()
        button_bar.addWidget(self.render_btn)

        editor_side = QVBoxLayout()
        editor_side.addWidget(QLabel("✏️ Notebook Editor"))
        editor_side.addWidget(self.editor)
        editor_side.addLayout(button_bar)
        editor_side.addWidget(QLabel("🔍 Rendered View"))
        editor_side.addWidget(self.viewer)

        right_panel = QWidget()
        right_panel.setLayout(editor_side)

        layout.addWidget(self.list, 1)
        layout.addWidget(right_panel, 3)

        self.load_sessions()
        self.setup_connections()

    def setup_connections(self):
        self.new_btn.clicked.connect(self.create_new)
        self.save_btn.clicked.connect(self.save_current)
        self.rename_btn.clicked.connect(self.rename_current)
        self.delete_btn.clicked.connect(self.delete_current)
        self.render_btn.clicked.connect(self.render_content)
        self.list.itemClicked.connect(self.load_selected)

    def create_new(self):
        self.current_session = NotebookSession()
        self.editor.clear()
        self.load_sessions()

    def save_current(self):
        if self.current_session:
            self.current_session.content = self.editor.toPlainText()
            self.manager.save_session(self.current_session)
            self.load_sessions()

    def rename_current(self):
        if not self.current_session:
            return
        title, ok = QInputDialog.getText(self, "Rename Notebook", "Title:", text=self.current_session.title)
        if ok and title:
            self.current_session.title = title
            self.save_current()

    def delete_current(self):
        if not self.current_session:
            return
        confirm = QMessageBox.question(self, "Delete", f"Delete notebook '{self.current_session.title}'?")
        if confirm == QMessageBox.Yes:
            self.manager.delete_session(self.current_session.session_id)
            self.current_session = None
            self.editor.clear()
            self.viewer.setHtml("")
            self.load_sessions()

    def load_sessions(self):
        self.list.clear()
        sessions = self.manager.get_all_sessions()
        for s in sessions:
            item = QListWidgetItem(s.title)
            item.setData(Qt.UserRole, s)
            self.list.addItem(item)

    def load_selected(self, item):
        session = item.data(Qt.UserRole)
        self.current_session = session
        self.editor.setPlainText(session.content)

    def render_content(self):
        if not self.current_session:
            return
        content = self.editor.toPlainText()
        html = markdown2.markdown(content)
        template = f"""
        <html>
        <head>
            <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
            <script type="text/javascript" id="MathJax-script" async
              src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
            </script>
        </head>
        <body>{html}</body>
        </html>
        """
        self.viewer.setHtml(template)
