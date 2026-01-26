# plugins/contract_plugin.py

import json
import os

from semantic_kernel.functions import kernel_function


class ContractIssuesPlugin:

    LOG_PATH = "data/contract_updates.json"

    def __init__(self):
        if os.path.exists(self.LOG_PATH):
            try:
                with open(self.LOG_PATH, "r", encoding="utf-8") as f:
                    self.log = json.load(f)
            except:
                self.log = []
        else:
            self.log = []

    def _save(self):
        os.makedirs(os.path.dirname(self.LOG_PATH), exist_ok=True)
        with open(self.LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.log, f, indent=2)

    @kernel_function(
        name="log_contract_issue",
        description="Logs contract-related issues for manual processes.",
    )
    async def log_contract_issue(self, issue_text: str, conversation_id: str) -> dict:

        entry = {"conversation_id": conversation_id, "issue_text": issue_text}
        self.log.append(entry)
        self._save()

        return {
            "intent": "ContractIssues",
            "status": "logged",
            "notes": "Contract issue recorded.",
        }
