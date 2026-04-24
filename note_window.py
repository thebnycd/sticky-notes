from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSizeGrip, QMenu, QMessageBox,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QAction, QPainter, QPen

from notes_manager import Note, NotesManager


COLORS = {
    "Жёлтый":    "#FEFF9C",
    "Розовый":   "#FFB3C1",
    "Голубой":   "#BAE1FF",
    "Зелёный":   "#BAFFC9",
    "Оранжевый": "#FFD9B4",
    "Лавандовый":"#E0BAFF",
}


class NoteWindow(QWidget):
    deleted = pyqtSignal(str)   # note_id
    pin_label_map = {"app": "Приложение", "window": "Окно"}

    def __init__(self, note: Note, manager: NotesManager):
        super().__init__()
        self.note = note
        self.manager = manager
        self._drag_pos: QPoint | None = None
        self._setup_ui()
        self._apply_color(note.color)
        self.setGeometry(note.x, note.y, note.width, note.height)

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setMinimumSize(160, 130)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Title bar ──────────────────────────────────────────────
        self.title_bar = QWidget()
        self.title_bar.setObjectName("titleBar")
        self.title_bar.setFixedHeight(30)
        self.title_bar.setCursor(Qt.CursorShape.SizeAllCursor)

        tb = QHBoxLayout(self.title_bar)
        tb.setContentsMargins(8, 2, 4, 2)
        tb.setSpacing(4)

        self.lbl_pin = QLabel()
        self.lbl_pin.setFont(QFont("Segoe UI", 8))
        self._update_pin_label()
        tb.addWidget(self.lbl_pin, 1)

        for text, slot in [("🎨", self._show_color_menu),
                            ("−",  self._hide_note),
                            ("✕",  self._delete_note)]:
            btn = QPushButton(text)
            btn.setFixedSize(22, 22)
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("tbBtn")
            if text == "−":
                btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        root.addWidget(self.title_bar)

        # ── Text area ──────────────────────────────────────────────
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.note.content)
        self.text_edit.setFont(QFont("Segoe UI", 10))
        self.text_edit.setFrameShape(QTextEdit.Shape.NoFrame)
        self.text_edit.setPlaceholderText("Напишите заметку…")
        self.text_edit.textChanged.connect(self._on_text_changed)
        root.addWidget(self.text_edit, 1)

        # ── Resize grip ────────────────────────────────────────────
        grip_row = QHBoxLayout()
        grip_row.setContentsMargins(0, 0, 2, 2)
        grip_row.addStretch()
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        grip_row.addWidget(grip)
        root.addLayout(grip_row)

    def _update_pin_label(self):
        kind = self.pin_label_map.get(self.note.pin_type, "")
        val = self.note.pin_value
        short = val if len(val) <= 28 else val[:25] + "…"
        self.lbl_pin.setText(f"📌 {kind}: {short}")

    def _apply_color(self, color: str):
        self.note.color = color
        dark = QColor(color).darker(118).name()
        text_color = "#333333"
        self.setStyleSheet(f"""
            NoteWindow {{
                background: {color};
                border: 1px solid {dark};
                border-radius: 5px;
            }}
            #titleBar {{
                background: {dark};
                border-radius: 5px 5px 0 0;
            }}
            QTextEdit {{
                background: transparent;
                border: none;
                padding: 4px 6px;
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
            }}
            #tbBtn {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {text_color};
                font-size: 11px;
            }}
            #tbBtn:hover {{
                background: rgba(0,0,0,0.18);
            }}
        """)

    # ── Slots ──────────────────────────────────────────────────────

    def _show_color_menu(self):
        menu = QMenu(self)
        for name, hex_color in COLORS.items():
            action = QAction(name, self)
            action.triggered.connect(lambda _, c=hex_color: self._change_color(c))
            menu.addAction(action)
        btn = self.sender()
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    def _change_color(self, color: str):
        self._apply_color(color)
        self.manager.update(self.note.id, color=color)

    def _on_text_changed(self):
        self.manager.update(self.note.id, content=self.text_edit.toPlainText())

    def _hide_note(self):
        self.manager.update(self.note.id, hidden=True)
        self.hide()

    def _delete_note(self):
        reply = QMessageBox.question(
            self, "Удалить заметку",
            "Удалить эту заметку навсегда?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete(self.note.id)
            self.deleted.emit(self.note.id)
            self.close()

    def reveal(self):
        """Show note and clear hidden flag."""
        self.manager.update(self.note.id, hidden=False)
        self.show()
        self.raise_()

    # ── Drag to move ───────────────────────────────────────────────

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton and
                self.title_bar.geometry().contains(event.pos())):
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        if self._drag_pos:
            self._drag_pos = None
            self._save_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._save_geometry()

    def _save_geometry(self):
        p, s = self.pos(), self.size()
        self.manager.update(
            self.note.id,
            x=p.x(), y=p.y(),
            width=s.width(), height=s.height(),
        )
