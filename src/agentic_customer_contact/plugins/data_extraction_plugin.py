import json
import logging
from pathlib import Path
from semantic_kernel.functions import kernel_function

from ..services.llm_service import LLMService

log = logging.getLogger(__name__)

class DataExtractionPlugin:

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="extract_data",
        description="Extracts structured fields (meter, personal data, tariff questions) from email text.",
    )
    async def extract_data(self, email_text: str) -> dict:
        raw_result = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"email_text": email_text},
        )
        try:
            return json.loads(raw_result)
        except ValueError:
            log.error(f"Invalid JSON in extraction. Will return empty dict!")
            # return {"error": "Invalid JSON in extraction"}
            return {}
