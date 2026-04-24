from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QRadioButton, QPushButton, QButtonGroup, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PinDialog(QDialog):
    def __init__(self, process_name: str, window_title: str, parent=None):
        super().__init__(parent)
        self.process_name = process_name
        self.window_title = window_title
        self.pin_type = "app"
        self.pin_value = process_name
        self._build()

    def _build(self):
        self.setWindowTitle("Прикрепить заметку")
        self.setFixedWidth(400)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 18, 20, 18)

        title = QLabel("Куда прикрепить заметку?")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # Option 1 — whole application
        app_short = self.process_name if len(self.process_name) <= 45 else self.process_name[:42] + "…"
        self.radio_app = QRadioButton(
            f"Для всего приложения\n        📁  {app_short}"
        )
        self.radio_app.setFont(QFont("Segoe UI", 10))
        self.radio_app.setChecked(True)

        # Option 2 — specific window/tab
        wt_short = self.window_title if len(self.window_title) <= 45 else self.window_title[:42] + "…"
        self.radio_window = QRadioButton(
            f"Для этого окна / вкладки\n        🪟  {wt_short}"
        )
        self.radio_window.setFont(QFont("Segoe UI", 10))

        group = QButtonGroup(self)
        group.addButton(self.radio_app)
        group.addButton(self.radio_window)

        layout.addWidget(self.radio_app)
        layout.addWidget(self.radio_window)
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

        ok = QPushButton("Создать")
        ok.setFixedWidth(100)
        ok.setDefault(True)
        ok.clicked.connect(self._accept)

        btn_row.addWidget(cancel)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    def _accept(self):
        if self.radio_app.isChecked():
            self.pin_type = "app"
            self.pin_value = self.process_name
        else:
            self.pin_type = "window"
            self.pin_value = self.window_title
        self.accept()
