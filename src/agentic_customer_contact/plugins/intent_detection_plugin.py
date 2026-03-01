"""Implement the intent detection Plugin."""

import json
import logging
import re
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
            expect_json=True,
        )
        try:
            parsed = self._parse_intents_json(raw_result)
            if isinstance(parsed, list):
                return self._normalize_intents(parsed)
            if isinstance(parsed, dict) and "intents" in parsed:
                intents = parsed.get("intents")
                if isinstance(intents, list):
                    return self._normalize_intents(intents)
            raise ValueError("Unexpected JSON shape for intent detection.")
        except json.JSONDecodeError:
            log.warning(
                f"semantic kernel service couldn't return a proper intent. Checking manually now."
            )
            return self._detect_intent_manually(email_text)
        except ValueError:
            log.warning(
                "Intent detection JSON shape invalid. Falling back to manual detection."
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

    @staticmethod
    def _normalize_intents(values: list) -> list[str]:
        """Normalize variants like ['{\"intents\": [...]}'] into plain intent names."""
        normalized: list[str] = []
        for item in values:
            if isinstance(item, str):
                stripped = item.strip()
                # Handle nested JSON encoded as string.
                if stripped.startswith("{") or stripped.startswith("["):
                    try:
                        nested = json.loads(stripped)
                        if isinstance(nested, dict) and isinstance(
                            nested.get("intents"), list
                        ):
                            normalized.extend(
                                [str(intent) for intent in nested["intents"]]
                            )
                            continue
                        if isinstance(nested, list):
                            normalized.extend([str(intent) for intent in nested])
                            continue
                    except json.JSONDecodeError:
                        pass
                normalized.append(stripped)
                continue
            normalized.append(str(item))
        return normalized

    @staticmethod
    def _parse_intents_json(raw_result: str) -> list[str] | dict:
        """Parse JSON for intent detection from plain or fenced model output."""
        raw = raw_result.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))

        start = min((i for i in [raw.find("["), raw.find("{")] if i != -1), default=-1)
        if start != -1:
            snippet = raw[start:]
            return json.loads(snippet)

        raise json.JSONDecodeError("No JSON payload found.", raw, 0)
