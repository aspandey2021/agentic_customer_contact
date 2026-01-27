"""Implement Email Writer class."""
import logging
from .. import EMAIL_FOLDER

log = logging.getLogger(__name__)


class EmailWriter:
    """Class to write final email to customer to a file."""
    def __init__(self, conversation_id: str):
        """Initialise.
        :param conversation_id: str identifier for the current conversation thread.
        """
        self.conversation_id = conversation_id
        self.base_folder = EMAIL_FOLDER

    def write_response(self, content: str, index: int) -> None:
        """Write the assistant's response to email_reply_N.txt.

        :param content: str assistant's response to write to email.
        :param index: int index of the email to be read.
        :return: None.
        """
        folder = self.base_folder / f"{self.conversation_id}"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"assistant_reply_{index}.txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        log.info(f"Assistant reply saved to {path}")
