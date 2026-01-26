from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..config.config import Intent


@dataclass
class SharedState:
    """Holds all state information for a multi-intent, multi-turn interaction."""

    conversation_id: str = "default_conversation"

    email_text: Optional[str] = None
    intents: List[Intent] = field(default_factory=list)

    extracted_data: Dict = field(default_factory=dict)

    auth_validated: bool = False
    auth_data: Dict = field(default_factory=dict)

    intent_results: Dict = field(default_factory=dict)

    history: List[Dict] = field(default_factory=list)

    def add_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
