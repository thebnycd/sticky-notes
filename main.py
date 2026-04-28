import sys
import os

import win32gui
from PyQt6.QtWidgets import QApplication, QDialog, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QAction
from PyQt6.QtGui import QPolygonF
from PyQt6.QtCore import Qt, QPoint, QPointF, QTimer

from notes_manager import NotesManager
from note_window import NoteWindow
from window_monitor import WindowMonitor
from pin_overlay import PinOverlay
from hotkey_manager import HotkeyThread, hotkey_to_str
from config_manager import ConfigManager
from settings_dialog import SettingsDialog

APP_NAME  = "Az Note"
DATA_DIR  = os.path.join(os.path.expanduser("~"), ".az_note")
DATA_PATH = os.path.join(DATA_DIR, "notes.json")
CFG_PATH  = os.path.join(DATA_DIR, "config.json")


def _build_tray_icon() -> QIcon:
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#BAE1FF"))
    p.setPen(QColor("#5BA8D4"))
    p.drawRoundedRect(4, 12, 56, 50, 5, 5)
    p.setBrush(QColor("#5BA8D4"))
    fold = QPolygonF([QPointF(4, 12), QPointF(24, 12), QPointF(4, 30)])
    p.drawPolygon(fold)
    p.setBrush(QColor("#E03030"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPoint(32, 8), 7, 7)
    p.setPen(QColor("#B02020"))
    p.drawLine(32, 15, 32, 24)
    p.setPen(QColor("#3A88BB"))
    for y in (30, 39, 48):
        p.drawLine(12, y, 52, y)
    p.end()
    return QIcon(pix)


class App:
    def __init__(self, qapp: QApplication):
        self.qapp = qapp
        self.config  = ConfigManager(CFG_PATH)
        self.manager = NotesManager(DATA_PATH)
        self.note_windows: dict[str, NoteWindow] = {}
        self.cur_process = ""
        self.cur_title   = ""
        self.cur_hwnd    = 0
        self._overlay: PinOverlay | None = None
        self._hotkey_thread: HotkeyThread | None = None
        self._pending: tuple[str, str, int] = ("", "", 0)

        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(250)
        self._debounce.timeout.connect(self._apply_window_change)

        self._setup_tray()
        self._load_notes()
        self._start_monitor()
        self._apply_hotkey(self.config.hotkey)

    # ── Tray ───────────────────────────────────────────────────────

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(_build_tray_icon(), self.qapp)
        hk = self.config.hotkey
        self.tray.setToolTip(f"{APP_NAME} — {hk} для прикрепления")

        menu = QMenu()
        act_pin = QAction("📌  Прикрепить заметку на окно", menu)
        act_pin.triggered.connect(self.start_pin_mode)
        menu.addAction(act_pin)
        menu.addSeparator()
        act_show = QAction("👁  Показать все заметки", menu)
        act_show.triggered.connect(self.show_all)
        menu.addAction(act_show)
        act_hide = QAction("🙈  Скрыть все заметки", menu)
        act_hide.triggered.connect(self.hide_all)
        menu.addAction(act_hide)
        act_delete_all = QAction("🗑  Удалить все заметки", menu)
        act_delete_all.triggered.connect(self.delete_all)
        menu.addAction(act_delete_all)
        menu.addSeparator()
        act_settings = QAction("⚙️  Настройки", menu)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)
        menu.addSeparator()
        act_quit = QAction("✕  Выход", menu)
        act_quit.triggered.connect(self.qapp.quit)
        menu.addAction(act_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.start_pin_mode()

    # ── Settings ───────────────────────────────────────────────────

    def open_settings(self):
        dlg = SettingsDialog(self.config)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if dlg.new_hotkey:
            new_hk = hotkey_to_str(dlg.new_hotkey)
            self.config.hotkey = new_hk
            self._apply_hotkey(new_hk)
            self.tray.setToolTip(f"{APP_NAME} — {new_hk} для прикрепления")

        self.config.font_size = dlg.new_font_size

        for win in self.note_windows.values():
            win.set_font_size(dlg.new_font_size)

    # ── Hotkey ─────────────────────────────────────────────────────

    def _apply_hotkey(self, hotkey_str: str):
        if self._hotkey_thread is not None:
            self._hotkey_thread.stop()
        self._hotkey_thread = HotkeyThread(hotkey_str)
        self._hotkey_thread.triggered.connect(self.start_pin_mode)
        self._hotkey_thread.start()

    # ── Pin mode ───────────────────────────────────────────────────

    def start_pin_mode(self):
        if self._overlay is not None:
            return
        self._overlay = PinOverlay()
        self._overlay.window_picked.connect(self._on_window_picked)
        self._overlay.cancelled.connect(self._on_pin_cancelled)

    def _on_pin_cancelled(self):
        self._overlay = None

    def _on_window_picked(self, process_name: str, title: str, hwnd: int):
        self._overlay = None
        try:
            rect = win32gui.GetWindowRect(hwnd)
            note_x = rect[2] - 330
            note_y = rect[1] + 930          # ~23-25 cm down from top
            note_y = min(note_y, rect[3] - 230)
        except Exception:
            note_x, note_y = 120, 120

        note = self.manager.create_note(
            content="", x=note_x, y=note_y,
            pin_type="window",
            pin_value=title,
        )
        win = self._make_window(note, visible=True)
        win.set_font_size(self.config.font_size)
        win.activateWindow()
        QTimer.singleShot(50, win.text_edit.setFocus)

    # ── Notes ──────────────────────────────────────────────────────

    def _load_notes(self):
        for note in self.manager.get_all():
            win = self._make_window(note, visible=False)
            win.set_font_size(self.config.font_size)

    def _make_window(self, note, visible: bool = False) -> NoteWindow:
        win = NoteWindow(note, self.manager)
        win.deleted.connect(self._on_deleted)
        self.note_windows[note.id] = win
        if visible:
            win.show()
            win.raise_()
        return win

    def show_all(self):
        for win in self.note_windows.values():
            win.reveal()

    def hide_all(self):
        for win in self.note_windows.values():
            win.hide()

    def delete_all(self):
        for note_id in list(self.note_windows.keys()):
            self.manager.delete(note_id)
            win = self.note_windows.pop(note_id, None)
            if win:
                win.close()

    def _on_deleted(self, note_id: str):
        self.note_windows.pop(note_id, None)

    # ── Window monitor ─────────────────────────────────────────────

    def _start_monitor(self):
        self.monitor = WindowMonitor()
        self.monitor.window_changed.connect(self._on_window_changed)
        self.monitor.start()

    def _on_window_changed(self, process_name: str, window_title: str, hwnd: int):
        self._pending = (process_name, window_title, hwnd)
        self._debounce.start()

    def _apply_window_change(self):
        process_name, window_title, hwnd = self._pending

        # If previous pinned window was CLOSED (X button) → delete its notes
        if self.cur_hwnd:
            prev_active = self.manager.get_for_window(self.cur_process, self.cur_title)
            if prev_active:
                try:
                    window_closed = not win32gui.IsWindow(self.cur_hwnd)
                    if window_closed:
                        for note in prev_active:
                            self.manager.delete(note.id)
                            win = self.note_windows.pop(note.id, None)
                            if win:
                                win.close()
                except Exception:
                    pass

        self.cur_process = process_name
        self.cur_title   = window_title
        self.cur_hwnd    = hwnd

        active_notes = self.manager.get_for_window(process_name, window_title)
        active_ids   = {n.id for n in active_notes}

        for note_id, win in self.note_windows.items():
            note = self.manager.notes.get(note_id)
            if note_id in active_ids and note and not note.hidden:
                win.show()
                win.raise_()
            else:
                win.hide()

    def cleanup(self):
        self.monitor.stop()
        if self._hotkey_thread:
            self._hotkey_thread.stop()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Ошибка", "Системный трей недоступен.")
        sys.exit(1)

    instance = App(app)
    result = app.exec()
    instance.cleanup()
    sys.exit(result)


if __name__ == "__main__":
    main()
