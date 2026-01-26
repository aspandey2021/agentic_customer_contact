# services/email_writer.py

import os


class EmailWriter:

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id

    def write_response(self, content: str, index: int):
        """
        Writes the assistant's response to email_reply_N.txt.
        """

        folder = f"data/emails/{self.conversation_id}"
        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, f"assistant_reply_{index}.txt")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n[Assistant reply saved to {path}]\n")
