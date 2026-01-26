import json
from pathlib import Path
import logging
from semantic_kernel.functions import kernel_function
from ..services.llm_service import LLMService

log = logging.getLogger(__name__)


class ProductInfoPlugin:
    """
    Plugin for getting specific product information based on user questions.
    """
    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        self.llm = llm_service
        self.prompt_path = prompt_path
        self.product_info = {
            "intent": "ProductInfoRequest",
            "status": '',
            "customer_question": '',
            "assistant_answer": '',
        }

    @kernel_function(
        name="process_product_info_request",
        description="Processes tariff/product info request in structured form.",
    )
    async def process_product_info_request(self, tariff_questions: str | None) -> dict:
        raw_result = await self.llm.run_template(prompt_path=self.prompt_path,
                                                   variables = {"customer_question": tariff_questions})
        self.product_info["customer_question"] = tariff_questions

        try:
            response = json.loads(raw_result)
            self.product_info["status"] = "success"
            self.product_info["assistant_answer"] = response
            return self.product_info

        except json.JSONDecodeError:
            log.warning(f"Could not extract relevant Product Info regarding the questions. "
                        f"Try again with some other questions.")

            self.product_info["status"] = "failed"
            self.product_info["assistant_answer"] = 'No info found.'
            return self.product_info

