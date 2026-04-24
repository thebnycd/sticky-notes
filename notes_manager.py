import json
import os
import uuid
from dataclasses import dataclass, asdict


@dataclass
class Note:
    id: str
    content: str
    x: int
    y: int
    width: int
    height: int
    pin_type: str   # "app" or "window"
    pin_value: str  # process name (e.g. "chrome.exe") or window title
    color: str = "#BAE1FF"
    hidden: bool = False


class NotesManager:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.notes: dict[str, Note] = {}
        self._load()
        self._reset_hidden()

    def _load(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.notes = {k: Note(**v) for k, v in data.items()}
            except Exception:
                self.notes = {}

    def _reset_hidden(self):
        changed = False
        for note in self.notes.values():
            if note.hidden:
                note.hidden = False
                changed = True
        if changed:
            self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in self.notes.items()},
                f, ensure_ascii=False, indent=2,
            )

    def create_note(
        self, content: str, x: int, y: int,
        pin_type: str, pin_value: str,
        width: int = 260, height: int = 200,
    ) -> Note:
        note_id = str(uuid.uuid4())
        note = Note(
            id=note_id, content=content,
            x=x, y=y, width=width, height=height,
            pin_type=pin_type, pin_value=pin_value,
        )
        self.notes[note_id] = note
        self.save()
        return note

    def update(self, note_id: str, **kwargs):
        if note_id in self.notes:
            for k, v in kwargs.items():
                setattr(self.notes[note_id], k, v)
            self.save()

    def delete(self, note_id: str):
        self.notes.pop(note_id, None)
        self.save()

    def get_for_window(self, process_name: str, window_title: str) -> list[Note]:
        result = []
        pn = process_name.lower()
        wt = window_title.lower()
        for note in self.notes.values():
            if note.pin_type == "app" and note.pin_value.lower() == pn:
                result.append(note)
            elif note.pin_type == "window":
                pv = note.pin_value.lower()
                # flexible match: one title contains the other
                if pv and (pv in wt or wt in pv):
                    result.append(note)
        return result

    def get_all(self) -> list[Note]:
        return list(self.notes.values())
