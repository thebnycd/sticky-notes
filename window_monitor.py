import os
from PyQt6.QtCore import QThread, pyqtSignal
import win32gui
import win32process
import psutil

OWN_PID = os.getpid()

# System windows that should hide all notes (taskbar, Start, desktop, etc.)
SYSTEM_CLASSES = frozenset({
    "Shell_TrayWnd",           # taskbar
    "Shell_SecondaryTrayWnd",  # taskbar on second monitor
    "Windows.UI.Core.CoreWindow",  # Start menu / Action Center
    "Progman",                 # desktop
    "WorkerW",                 # desktop worker
    "DV2ControlHost",          # Start menu search
    "TaskListThumbnailWnd",    # taskbar thumbnail preview
})


class WindowMonitor(QThread):
    window_changed = pyqtSignal(str, str, int)  # process_name, window_title, hwnd

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        last_hwnd = None
        while self._running:
            hwnd = win32gui.GetForegroundWindow()

            # No foreground window = all windows minimised / desktop shown
            if not hwnd:
                if last_hwnd != 0:
                    last_hwnd = 0
                    self.window_changed.emit("", "", 0)
                self.msleep(300)
                continue

            if hwnd != last_hwnd:
                pid = self._get_pid(hwnd)
                if pid == OWN_PID:
                    self.msleep(300)
                    continue
                last_hwnd = hwnd

                try:
                    cls = win32gui.GetClassName(hwnd)
                except Exception:
                    cls = ""

                if cls in SYSTEM_CLASSES:
                    self.window_changed.emit("", "", 0)
                else:
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
