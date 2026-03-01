"""Implement LLM Service class."""

import json
from pathlib import Path
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments


class LLMService:
    """Class which is a wrapper around Semantic Kernel to load prompt templates,
    inject variables, and call Azure OpenAI via Semantic Kernel.
    """

    def __init__(self, kernel: Kernel):
        """Initialise.

        :param kernel: Kernel object containing relevant Azure Services and plugins.
        """
        self.kernel = kernel

    async def run_template(
        self,
        prompt_path: Path | str,
        variables: dict[str, Any],
        expect_json: bool = False,
    ) -> str:
        """Load a '.prompt' template file and runs it with the provided variables.

        :param prompt_path: path to the respective prompt file.
        :param variables: variables to passed to the LLM prompt template.
        :param expect_json: when True, asks model for JSON-object output mode.
        :return: response from the LLM service.
        """
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        settings = OpenAIChatPromptExecutionSettings(service_id="azure_openai_chat")
        if expect_json:
            settings.response_format = {"type": "json_object"}

        arguments = KernelArguments(**variables, settings=settings)

        # Let SK render template and execute the selected service.
        result = await self.kernel.invoke_prompt(
            prompt=prompt_text,
            arguments=arguments,
        )
        value = result.value if hasattr(result, "value") else result
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=self._json_default)
        if hasattr(value, "content"):
            return str(getattr(value, "content"))
        return str(value)

    @staticmethod
    def _json_default(obj: Any) -> str:
        """Serialize Semantic Kernel content objects safely for plugin parsing."""
        if hasattr(obj, "content"):
            return str(getattr(obj, "content"))
        return str(obj)
