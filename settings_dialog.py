from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QSpinBox, QCheckBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence


class HotkeyCapture(QLineEdit):
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
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Alt,
                   Qt.Key.Key_Shift, Qt.Key.Key_Meta, Qt.Key.Key_unknown):
            return
        parts = []
        if mods & Qt.KeyboardModifier.ControlModifier: parts.append("Ctrl")
        if mods & Qt.KeyboardModifier.AltModifier:     parts.append("Alt")
        if mods & Qt.KeyboardModifier.ShiftModifier:   parts.append("Shift")
        if mods & Qt.KeyboardModifier.MetaModifier:    parts.append("Win")
        key_name = QKeySequence(key).toString()
        if key_name:
            parts.append(key_name.upper())
        if len(parts) >= 2:
            self.setText("+".join(parts))


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.new_hotkey = config.hotkey
        self.new_font_size = config.font_size
        self.new_close_with_window = config.close_with_window
        self._build()

    def _build(self):
        self.setWindowTitle("Настройки — Az Note")
        self.setFixedWidth(380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("⚙️  Настройки")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addWidget(self._sep())

        # ── Hotkey ─────────────────────────────────────────
        layout.addWidget(self._section_label("Горячая клавиша для прикрепления заметки:"))
        self.capture = HotkeyCapture(self.config.hotkey)
        layout.addWidget(self.capture)
        hint = QLabel("Кликните в поле и нажмите нужную комбинацию")
        hint.setFont(QFont("Segoe UI", 8))
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        layout.addWidget(self._sep())

        # ── Font size ───────────────────────────────────────
        layout.addWidget(self._section_label("Размер шрифта в заметках:"))
        font_row = QHBoxLayout()
        self.spin_font = QSpinBox()
        self.spin_font.setRange(7, 32)
        self.spin_font.setValue(self.config.font_size)
        self.spin_font.setSuffix("  пт")
        self.spin_font.setFixedWidth(100)
        self.spin_font.setFixedHeight(34)
        font_row.addWidget(self.spin_font)
        font_row.addStretch()
        layout.addLayout(font_row)

        layout.addWidget(self._sep())

        # ── Close with window ───────────────────────────────
        self.chk_close = QCheckBox(
            "Скрывать заметку когда окно закрывается / сворачивается"
        )
        self.chk_close.setFont(QFont("Segoe UI", 10))
        self.chk_close.setChecked(self.config.close_with_window)
        self.chk_close.setWordWrap(True)
        layout.addWidget(self.chk_close)

        layout.addStretch()
        layout.addWidget(self._sep())

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

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 10))
        lbl.setWordWrap(True)
        return lbl

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    def _save(self):
        self.new_hotkey           = self.capture.text()
        self.new_font_size        = self.spin_font.value()
        self.new_close_with_window = self.chk_close.isChecked()
        self.accept()
