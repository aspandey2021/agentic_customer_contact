"""Implement the product info Plugin."""

import json
import logging
from pathlib import Path

from semantic_kernel.functions import kernel_function

from ..services.llm_service import LLMService

log = logging.getLogger(__name__)


class ProductInfoPlugin:
    """Class for plugin to get the specific product information based on customer questions."""

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        """Initialise.

        :param llm_service: corresponding Azure service bound to the build kernel.
        :param prompt_path: Path to the product info prompt file.
        """
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="process_product_info_request",
        description="Processes tariff/product info request in structured form.",
    )
    async def process_product_info_request(self, tariff_questions: str | None) -> dict:
        """Built the extract data plugin function.

        :param tariff_questions: customer questions from the customer email.
        :return: dict containing the generated product info, the questions and status.
        """
        raw_result = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"customer_question": tariff_questions},
        )
        product_info = {
            "intent": "ProductInfoRequest",
            "status": "",
            "customer_question": tariff_questions,
            "assistant_answer": "",
        }

        try:
            response = json.loads(raw_result)
            product_info["status"] = "success"
            product_info["assistant_answer"] = response
            return product_info

        except json.JSONDecodeError:
            log.warning("Product info response was non-JSON. Returning plain text.")

            product_info["status"] = "success"
            product_info["assistant_answer"] = raw_result
            return product_info
