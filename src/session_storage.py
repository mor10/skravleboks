import json
import os
from datetime import datetime

class SessionStorage:
    def __init__(self, path="session.json"):
        self.path = path
        self.history = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []
        else:
            self.history = []

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def add_message(self, role, text):
        self.history.append({
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def get_history(self):
        return self.history
