import os
from PyQt6.QtCore import QThread, pyqtSignal
import win32gui
import win32process
import psutil

OWN_PID = os.getpid()


class WindowMonitor(QThread):
    window_changed = pyqtSignal(str, str, int)  # process_name, window_title, hwnd

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        last_hwnd = None
        while self._running:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd and hwnd != last_hwnd:
                pid = self._get_pid(hwnd)
                if pid == OWN_PID:
                    # our own note window gained focus — ignore
                    self.msleep(300)
                    continue
                last_hwnd = hwnd
                title = win32gui.GetWindowText(hwnd)
                process_name = self._get_process_name(pid)
                self.window_changed.emit(process_name, title, hwnd)
            self.msleep(300)

    def _get_pid(self, hwnd: int) -> int:
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception:
            return -1

    def _get_process_name(self, pid: int) -> str:
        try:
            return psutil.Process(pid).name()
        except Exception:
            return ""

    def stop(self):
        self._running = False
        self.wait()
