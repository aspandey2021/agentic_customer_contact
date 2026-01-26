import json
import os
from typing import Dict, List

from ..config.config import HISTORY_FOLDER


class ConversationHistory:

    @staticmethod
    def _path(conversation_id: str) -> str:
        return os.path.join(HISTORY_FOLDER, f"{conversation_id}.json")

    @staticmethod
    def load(conversation_id: str) -> List[Dict]:
        path = ConversationHistory._path(conversation_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(conversation_id: str, history: List[Dict]):
        os.makedirs(HISTORY_FOLDER, exist_ok=True)
        with open(
            ConversationHistory._path(conversation_id), "w", encoding="utf-8"
        ) as f:
            json.dump(history, f, indent=2)
