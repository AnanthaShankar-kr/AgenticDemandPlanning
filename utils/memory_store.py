import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class MemoryStore:
    _instance = None

    def __new__(cls, filepath: str = "data/memory_store.json"):
        if cls._instance is None:
            cls._instance = super(MemoryStore, cls).__new__(cls)
            cls._instance.filepath = filepath
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"[MemoryStore] Error loading memory: {e}")
                self.data = {"interactions": [], "insights": {}}
        else:
            self.data = {"interactions": [], "insights": {}}

    def _save(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[MemoryStore] Error saving memory: {e}")

    def log_interaction(self, user_query: str, agent_response: str, agent_name: str):
        """Logs a chat interaction."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "user_query": user_query,
            "agent_response": agent_response
        }
        self.data["interactions"].append(interaction)
        self._save()

    def save_insight(self, key: str, value: str) -> str:
        """Saves a specific insight or fact."""
        self.data["insights"][key] = value
        self._save()
        return f"Insight saved: {key} = {value}"

    def get_insight(self, key: str) -> str:
        """Retrieves a specific insight."""
        return self.data["insights"].get(key, "Insight not found.")

    def get_all_insights(self) -> Dict[str, str]:
        return self.data["insights"]

    def get_all_interactions(self) -> List[Dict]:
        return self.data["interactions"]
