"""Implement Handler Class to handle different intents."""

from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments

from ..config.config import Intent


class HandlerOfIntents:
    """Handler Class to handle different intents."""

    def __init__(self, kernel: Kernel, conversation_id: str) -> None:
        """Initialise the Handler.

        :param kernel: current semantic kernel containing the plugins.
        :param conversation_id: str identifier for the current conversation thread.
        """
        self.kernel = kernel
        self.conversation_id = conversation_id

    async def handle_meter_reading(
        self, intent: Intent, extracted: dict
    ) -> [Intent, Any]:
        """Implement handler to call meter reading plugin.

        :param intent: str, Intent which needs to be handled.
        :param extracted: extracted customer data from email, like meter reading, personal data etc.
        :return: meter reading intent and value of meter reading.
        """
        result = await self.kernel.invoke(
            plugin_name="MeterReadingPlugin",
            function_name="save_meter_reading",
            other_arguments={
                "meter_number": extracted.get("meter_number"),
                "meter_reading": extracted.get("meter_reading"),
                "conversation_id": self.conversation_id,
            },
        )
        return intent, result.value

    async def handle_product_info(
        self, intent: Intent, extracted: dict
    ) -> [Intent, Any]:
        """Implement handler to call product info plugin.

        :param intent: str, Intent which needs to be handled.
        :param extracted: extracted customer data from email, like meter reading, personal data etc.
        :return: product info intent and relevant product info generated from LLM service.
        """
        result = await self.kernel.invoke(
            plugin_name="ProductInfoPlugin",
            function_name="process_product_info_request",
            arguments=KernelArguments(
                tariff_questions=extracted.get("tariff_questions")
            ),
        )
        return intent, result.value
