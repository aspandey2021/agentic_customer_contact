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
        self.product_info = {
            "intent": "ProductInfoRequest",
            "status": "",
            "customer_question": "",
            "assistant_answer": "",
        }

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
        self.product_info["customer_question"] = tariff_questions

        try:
            response = json.loads(raw_result)
            self.product_info["status"] = "success"
            self.product_info["assistant_answer"] = response
            return self.product_info

        except json.JSONDecodeError:
            log.warning(
                f"Could not extract relevant Product Info regarding the questions. "
                f"Try again with some other questions."
            )

            self.product_info["status"] = "failed"
            self.product_info["assistant_answer"] = "No info found."
            return self.product_info
