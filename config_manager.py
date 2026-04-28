import json
import os

DEFAULTS = {
    "hotkey": "Alt+Q",
    "font_size": 10,
}


class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.data: dict = dict(DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def hotkey(self) -> str:
        return self.data.get("hotkey", DEFAULTS["hotkey"])

    @hotkey.setter
    def hotkey(self, value: str):
        self.data["hotkey"] = value
        self.save()

    @property
    def font_size(self) -> int:
        return int(self.data.get("font_size", DEFAULTS["font_size"]))

    @font_size.setter
    def font_size(self, value: int):
        self.data["font_size"] = value
        self.save()
