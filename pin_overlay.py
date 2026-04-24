import os
import win32gui
import win32con
import win32process
import psutil

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QColor, QFont, QCursor

OWN_PID = os.getpid()


class PinOverlay(QWidget):
    """Fullscreen transparent overlay — user clicks a window to pin a note."""
    window_picked = pyqtSignal(str, str, int)   # process_name, title, hwnd
    cancelled     = pyqtSignal()

    def __init__(self):
        super().__init__()
        # Span all monitors
        vg = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(vg)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 50))

        text = "📌  Кликните на нужное окно  •  Esc — отмена"
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        fm   = p.fontMetrics()
        tw   = fm.horizontalAdvance(text)
        th   = fm.height()
        pad  = 14
        rx   = (self.width() - tw) // 2 - pad
        ry   = 28

        p.setBrush(QColor(20, 20, 20, 200))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(rx, ry, tw + pad * 2, th + pad, 8, 8)

        p.setPen(QColor(255, 255, 255, 240))
        p.drawText(rx + pad, ry + th, text)
        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            gpos = event.globalPosition().toPoint()
            self.hide()
            QTimer.singleShot(100, lambda: self._pick(gpos.x(), gpos.y()))
        else:
            self._cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._cancel()

    def _cancel(self):
        self.close()
        self.cancelled.emit()

    def _pick(self, x: int, y: int):
        try:
            hwnd = win32gui.WindowFromPoint((x, y))
            root = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            if root and win32gui.IsWindowVisible(root):
                hwnd = root

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == OWN_PID:
                self._cancel()
                return

            title        = win32gui.GetWindowText(hwnd)
            process_name = psutil.Process(pid).name()

            if not process_name:
                self._cancel()
                return

            self.window_picked.emit(process_name, title, hwnd)
        except Exception:
            self.cancelled.emit()
        finally:
            self.close()
