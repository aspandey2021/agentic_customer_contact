import json
import logging
from pathlib import Path
from semantic_kernel.functions import kernel_function
from ..config.config import Intent
from ..services.llm_service import LLMService

log = logging.getLogger(__name__)

class IntentDetectionPlugin:
    """
    Plugin for detecting high-level customer intents.
    """

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="detect_intents",
        description="Detects customer intents from an email body.",
    )
    async def detect_intents(self, email_text: str) -> list[str]:

        raw_result = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"email_text": email_text},
        )

        try:
            return json.loads(raw_result)
        except json.JSONDecodeError:
            log.warning(f"semantic kernel service couldn't return a proper intent. Checking manually now.")
            return self._detect_intent_manually(email_text)

    @staticmethod
    def _detect_intent_manually(email_text: str) -> [Intent]:
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
