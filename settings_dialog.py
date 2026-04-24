from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence


class HotkeyCapture(QLineEdit):
    """Read-only field that captures a key combination on key press."""

    def __init__(self, initial: str = ""):
        super().__init__()
        self.setReadOnly(True)
        self.setText(initial)
        self.setPlaceholderText("Нажмите комбинацию клавиш…")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.setFixedHeight(38)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # Ignore standalone modifier keys
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Alt,
            Qt.Key.Key_Shift, Qt.Key.Key_Meta,
            Qt.Key.Key_unknown,
        ):
            return

        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier:
            parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.AltModifier:
            parts.append("Alt")
        if mods & Qt.KeyboardModifier.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.KeyboardModifier.MetaModifier:
            parts.append("Win")

        key_name = QKeySequence(key).toString()
        if key_name:
            parts.append(key_name.upper())

        if len(parts) >= 2:  # require at least one modifier + one key
            self.setText("+".join(parts))


class SettingsDialog(QDialog):
    def __init__(self, current_hotkey: str, parent=None):
        super().__init__(parent)
        self.new_hotkey = current_hotkey
        self._build(current_hotkey)

    def _build(self, current_hotkey: str):
        self.setWindowTitle("Настройки — Az Note")
        self.setFixedWidth(360)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("⚙️  Настройки")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Hotkey section
        lbl = QLabel("Горячая клавиша для прикрепления заметки:")
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self.capture = HotkeyCapture(current_hotkey)
        layout.addWidget(self.capture)

        hint = QLabel("Кликните в поле и нажмите нужную комбинацию")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addStretch()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel = QPushButton("Отмена")
        cancel.setFixedWidth(100)
        cancel.clicked.connect(self.reject)

        save = QPushButton("Сохранить")
        save.setFixedWidth(100)
        save.setDefault(True)
        save.clicked.connect(self._save)

        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _save(self):
        self.new_hotkey = self.capture.text()
        self.accept()
