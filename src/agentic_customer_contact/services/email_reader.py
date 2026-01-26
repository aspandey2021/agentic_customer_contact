# services/email_reader.py

import os

from ..config.config import EMAIL_FOLDER


class EmailReader:

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id

    def load_email(self, index: int) -> str:
        """
        Loads email_N.txt for the given conversation.
        Example path: data/emails/{conversation_id}/email_1.txt
        """

        folder = os.path.join(EMAIL_FOLDER, self.conversation_id)
        path = os.path.join(folder, f"email_{index}.txt")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Email file missing: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()
