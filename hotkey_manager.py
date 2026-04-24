import ctypes
import ctypes.wintypes
from PyQt6.QtCore import QThread, pyqtSignal

WM_HOTKEY  = 0x0312
WM_QUIT    = 0x0012
MOD_NOREPEAT = 0x4000

# Modifier names → Windows modifier flags
MOD_MAP = {
    "ctrl":    0x0002,
    "control": 0x0002,
    "alt":     0x0001,
    "shift":   0x0004,
    "win":     0x0008,
    "windows": 0x0008,
}

# Key names → Windows virtual key codes
VK_MAP: dict[str, int] = {
    **{chr(0x41 + i): 0x41 + i for i in range(26)},   # A-Z
    **{str(i): 0x30 + i for i in range(10)},            # 0-9
    "F1":  0x70, "F2":  0x71, "F3":  0x72, "F4":  0x73,
    "F5":  0x74, "F6":  0x75, "F7":  0x76, "F8":  0x77,
    "F9":  0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "SPACE": 0x20, "TAB": 0x09, "RETURN": 0x0D,
    "HOME": 0x24, "END": 0x23, "PRIOR": 0x21, "NEXT": 0x22,
    "INSERT": 0x2D, "DELETE": 0x2E,
}


def parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """'Alt+Q' → (modifiers, vk_code)  returns (0,0) on failure."""
    modifiers = MOD_NOREPEAT
    vk = 0
    for part in hotkey_str.replace(" ", "").split("+"):
        pl = part.lower()
        pu = part.upper()
        if pl in MOD_MAP:
            modifiers |= MOD_MAP[pl]
        elif pu in VK_MAP:
            vk = VK_MAP[pu]
    return modifiers, vk


def hotkey_to_str(hotkey_str: str) -> str:
    """Normalise 'alt+q' → 'Alt+Q'."""
    parts = []
    for part in hotkey_str.replace(" ", "").split("+"):
        pl = part.lower()
        if pl in ("ctrl", "control"):
            parts.append("Ctrl")
        elif pl == "alt":
            parts.append("Alt")
        elif pl == "shift":
            parts.append("Shift")
        elif pl in ("win", "windows"):
            parts.append("Win")
        else:
            parts.append(part.upper())
    return "+".join(parts)


class HotkeyThread(QThread):
    triggered = pyqtSignal()

    HOTKEY_ID = 9001

    def __init__(self, hotkey_str: str):
        super().__init__()
        self.hotkey_str = hotkey_str
        self._tid = 0

    def run(self):
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        mods, vk = parse_hotkey(self.hotkey_str)
        if not vk:
            return
        if not ctypes.windll.user32.RegisterHotKey(None, self.HOTKEY_ID, mods, vk):
            return

        msg = ctypes.wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == self.HOTKEY_ID:
                self.triggered.emit()

        ctypes.windll.user32.UnregisterHotKey(None, self.HOTKEY_ID)

    def stop(self):
        if self._tid:
            ctypes.windll.user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
        self.wait()
