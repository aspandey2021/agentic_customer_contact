"""Implement the conversation history class."""

import json
import logging
import os
from typing import Dict, List

from .. import HISTORY_FOLDER

log = logging.getLogger(__name__)


class ConversationHistory:
    """Class to handle conversation histories."""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.base_folder = HISTORY_FOLDER

    def load(self, conversation_id: str) -> List[Dict] | None:
        """Load conversation history.

        :param conversation_id: str identifier for the current conversation thread.
        :return: extracted list of dict containing conversation history.
        """
        path = self.base_folder / f"{conversation_id}.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            log.error(f"{path} not found!")
            return None

    def save(self, history: List[Dict]) -> None:
        """Save conversation history to base folder / {conversation_id}.json file.

        :param history: history to be saved.
        :return: None.
        """
        os.makedirs(self.base_folder, exist_ok=True)
        path = self.base_folder / f"{self.conversation_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
