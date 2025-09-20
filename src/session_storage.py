import json
import os
from datetime import datetime

class SessionStorage:
    def __init__(self, path="session.json", max_messages: int | None = None):
        self.path = path
        # Allow environment variable override (e.g., SKRAVLE_MAX_HISTORY=40)
        if max_messages is None:
            try:
                env_val = os.getenv("SKRAVLE_MAX_HISTORY")
                max_messages = int(env_val) if env_val else None
            except ValueError:
                max_messages = None
        self.max_messages = max_messages
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
        self._prune_if_needed()
        self.save()

    def _prune_if_needed(self):
        if self.max_messages is not None and len(self.history) > self.max_messages:
            # Keep only the most recent max_messages
            self.history = self.history[-self.max_messages:]

    def get_history(self):
        return self.history
