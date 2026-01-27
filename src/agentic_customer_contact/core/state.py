"""Implement the Shared State class."""

from dataclasses import dataclass, field
from typing import Optional

from ..config.config import Intent


@dataclass
class SharedState:
    """Class that holds all state information for a multi-intent, multi-turn interaction."""

    conversation_id: str = "default_conversation"
    email_text: Optional[str] = None
    intents: list[Intent] = field(default_factory=list)
    extracted_data: dict = field(default_factory=dict)
    auth_validated: bool = False
    auth_data: dict = field(default_factory=dict)
    intent_results: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def add_history(self, role: str, content: str) -> None:
        """Update shared state history.

        :param role: role as either customer or assistant.
        :param content: conversation content to be updated into history.
        :return: None.
        """
        self.history.append({"role": role, "content": content})
