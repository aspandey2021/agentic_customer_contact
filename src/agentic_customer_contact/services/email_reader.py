"""Implement Email Reader class."""

import logging

from .. import EMAIL_FOLDER

log = logging.getLogger(__name__)


class EmailReader:
    """Class to read customer emails."""

    def __init__(self, conversation_id: str):
        """Initialise.

        :param conversation_id: str identifier for the current conversation thread.
        """
        self.conversation_id = conversation_id
        self.base_folder = EMAIL_FOLDER

    def load_email(self, index: int) -> str:
        """Load email_N.txt for the given conversation.
        Example path: data/emails/{conversation_id}/email_1.txt

        :param index: int index of the email to be read.
        :return: str content of the email.
        """
        path = self.base_folder / f"{self.conversation_id}" / f"email_{index}.txt"

        if not path.exists():
            raise FileNotFoundError(f"Email file missing: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()
