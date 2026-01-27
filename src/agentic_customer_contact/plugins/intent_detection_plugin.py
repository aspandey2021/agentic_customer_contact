"""Implement the intent detection Plugin."""

import json
import logging
from pathlib import Path

from semantic_kernel.functions import kernel_function

from ..config.config import Intent
from ..services.llm_service import LLMService

log = logging.getLogger(__name__)


class IntentDetectionPlugin:
    """Class for plugin to detect the intents contained in the customer email."""

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        """Initialise.

        :param llm_service: corresponding Azure service bound to the build kernel.
        :param prompt_path: Path to the intent detection prompt file.
        """
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="detect_intents",
        description="Detects customer intents from an email body.",
    )
    async def detect_intents(self, email_text: str) -> list[str]:
        """Built the detect intents plugin function.

        :param email_text: string content of the customer email.
        :return: list of detected intents.
        """
        raw_result = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"email_text": email_text},
        )
        try:
            return json.loads(raw_result)
        except json.JSONDecodeError:
            log.warning(
                f"semantic kernel service couldn't return a proper intent. Checking manually now."
            )
            return self._detect_intent_manually(email_text)

    @staticmethod
    def _detect_intent_manually(email_text: str) -> [Intent]:
        """Manually detect intents, if the plugin couldn't generate any proper response.

        :param email_text: string content of the customer email.
        :return: list of detected intents.
        """
        intents = []
        keywords = {
            "MeterReadingSubmission": ["meter", "reading", "kwh"],
            "PersonalDataChange": [
                "address",
                "personal data",
                "birthday",
                "change",
            ],
            "ContractIssues": ["contract", "terminate", "switch", "duration"],
            "ProductInfoRequest": ["tariff", "product", "plan", "price"],
            "GeneralFeedback": ["feedback", "thanks", "complaint", "praise"],
        }
        for intent, keys in keywords.items():
            if any(k.lower() in email_text.lower() for k in keys):
                intents.append(intent)
        return intents
