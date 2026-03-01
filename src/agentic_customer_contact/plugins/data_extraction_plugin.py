"""Implement the data extraction Plugin."""

import json
import logging
import re
from pathlib import Path

from semantic_kernel.functions import kernel_function

from ..services.llm_service import LLMService

log = logging.getLogger(__name__)


class DataExtractionPlugin:
    """Class to extract the relevant customer data from email, like meter number, personal data etc."""

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        """Initialise.

        :param llm_service: corresponding Azure service bound to the build kernel.
        :param prompt_path: Path to the data extraction prompt file.
        """
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="extract_data",
        description="Extracts structured fields (meter, personal data, tariff questions) from email text.",
    )
    async def extract_data(self, email_text: str) -> dict:
        """Built the extract data plugin function.

        :param email_text: string content of the customer email.
        :return: LLM generated reply.
        """
        raw_result = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"email_text": email_text},
            expect_json=True,
        )
        try:
            parsed = self._parse_extraction_json(raw_result)
            normalized = self._normalize_extraction_payload(parsed)
            if isinstance(normalized, dict):
                return normalized
            raise ValueError("Extraction result is not a JSON object.")
        except ValueError:
            log.error("Invalid JSON in extraction. Will return empty dict!")
            return {}

    @staticmethod
    def _parse_extraction_json(raw_result: str):
        """Parse extraction payload from plain or fenced model output."""
        raw = raw_result.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))

        obj_start = raw.find("{")
        obj_end = raw.rfind("}")
        if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
            snippet = raw[obj_start : obj_end + 1]
            return json.loads(snippet)

        raise ValueError("No parseable JSON object found in extraction output.")

    @staticmethod
    def _normalize_extraction_payload(payload):
        """Normalize nested extraction output variants into a dict."""
        if isinstance(payload, dict):
            # Handle wrappers like {"data": {...}} or {"extracted_data": {...}}.
            for key in ("data", "extracted_data", "result"):
                nested = payload.get(key)
                if isinstance(nested, dict):
                    return nested
            return payload

        if isinstance(payload, list):
            for item in payload:
                normalized = DataExtractionPlugin._normalize_extraction_payload(item)
                if isinstance(normalized, dict):
                    return normalized
            return None

        if isinstance(payload, str):
            stripped = payload.strip()
            if stripped.startswith("{") or stripped.startswith("["):
                try:
                    nested = json.loads(stripped)
                except json.JSONDecodeError:
                    return None
                return DataExtractionPlugin._normalize_extraction_payload(nested)

        return None
