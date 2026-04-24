import sys
import os

import win32gui
from PyQt6.QtWidgets import (
    QApplication, QDialog, QSystemTrayIcon, QMenu, QMessageBox,
)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont, QAction
from PyQt6.QtCore import Qt, QPoint

from notes_manager import NotesManager
from note_window import NoteWindow
from window_monitor import WindowMonitor
from pin_dialog import PinDialog


DATA_PATH = os.path.join(os.path.expanduser("~"), ".sticky_notes", "notes.json")


def _build_tray_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # note body
    p.setBrush(QColor("#FEFF9C"))
    p.setPen(QColor("#C8C800"))
    p.drawRoundedRect(4, 12, 56, 50, 5, 5)

    # folded corner
    p.setBrush(QColor("#D4D400"))
    from PyQt6.QtGui import QPolygonF
    from PyQt6.QtCore import QPointF
    fold = QPolygonF([QPointF(4, 12), QPointF(24, 12), QPointF(4, 30)])
    p.drawPolygon(fold)

    # pin head
    p.setBrush(QColor("#E03030"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPoint(32, 8), 7, 7)
    p.setPen(QColor("#B02020"))
    p.setBrush(QColor("#C02020"))
    p.drawLine(32, 15, 32, 24)

    # lines on note
    p.setPen(QColor("#999900"))
    for y in (30, 39, 48):
        p.drawLine(12, y, 52, y)

    p.end()
    return QIcon(pix)


class App:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.manager = NotesManager(DATA_PATH)
        self.note_windows: dict[str, NoteWindow] = {}

        # currently active external window
        self.cur_process = ""
        self.cur_title = ""
        self.cur_hwnd = 0

        self._setup_tray()
        self._load_notes()
        self._start_monitor()

    # ── Tray ───────────────────────────────────────────────────────

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(_build_tray_icon(), self.qapp)
        self.tray.setToolTip("Sticky Notes")

        menu = QMenu()

        act_new = QAction("📝  Новая заметка для текущего окна", menu)
        act_new.triggered.connect(self.new_note)
        menu.addAction(act_new)

        menu.addSeparator()

        act_show = QAction("👁  Показать все заметки", menu)
        act_show.triggered.connect(self.show_all)
        menu.addAction(act_show)

        act_hide = QAction("🙈  Скрыть все заметки", menu)
        act_hide.triggered.connect(self.hide_all)
        menu.addAction(act_hide)

        menu.addSeparator()

        act_quit = QAction("✕  Выход", menu)
        act_quit.triggered.connect(self.qapp.quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.new_note()

    # ── Notes ──────────────────────────────────────────────────────

    def _load_notes(self):
        for note in self.manager.get_all():
            self._make_window(note, visible=False)

    def _make_window(self, note, visible: bool = False) -> NoteWindow:
        win = NoteWindow(note, self.manager)
        win.deleted.connect(self._on_deleted)
        self.note_windows[note.id] = win
        if visible:
            win.show()
            win.raise_()
        return win

    def new_note(self):
        if not self.cur_process and not self.cur_title:
            QMessageBox.information(
                None, "Нет активного окна",
                "Сначала переключитесь на нужное окно,\nзатем нажмите «Новая заметка».",
            )
            return

        dlg = PinDialog(self.cur_process, self.cur_title)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        x, y = self._note_spawn_pos()
        note = self.manager.create_note(
            content="", x=x, y=y,
            pin_type=dlg.pin_type,
            pin_value=dlg.pin_value,
        )
        win = self._make_window(note, visible=True)
        win.text_edit.setFocus()

    def _note_spawn_pos(self) -> tuple[int, int]:
        try:
            rect = win32gui.GetWindowRect(self.cur_hwnd)
            return rect[0] + 10, rect[1] + 40
        except Exception:
            return 120, 120

    def show_all(self):
        for win in self.note_windows.values():
            win.reveal()

    def hide_all(self):
        for win in self.note_windows.values():
            win.hide()

    def _on_deleted(self, note_id: str):
        self.note_windows.pop(note_id, None)

    # ── Window monitor ─────────────────────────────────────────────

    def _start_monitor(self):
        self.monitor = WindowMonitor()
        self.monitor.window_changed.connect(self._on_window_changed)
        self.monitor.start()

    def _on_window_changed(self, process_name: str, window_title: str, hwnd: int):
        self.cur_process = process_name
        self.cur_title = window_title
        self.cur_hwnd = hwnd

        active_notes = self.manager.get_for_window(process_name, window_title)
        active_ids = {n.id for n in active_notes}

        for note_id, win in self.note_windows.items():
            note = self.manager.notes.get(note_id)
            if note_id in active_ids and note and not note.hidden:
                win.show()
                win.raise_()
            else:
                win.hide()

    def cleanup(self):
        self.monitor.stop()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "Ошибка", "Системный трей недоступен.")
        sys.exit(1)

    instance = App(app)
    result = app.exec()
    instance.cleanup()
    sys.exit(result)


if __name__ == "__main__":
    main()
