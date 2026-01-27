"""Implement LLM Service class."""
from pathlib import Path
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings


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
        self, prompt_path: Path | str, variables: dict[str, Any]
    ) -> str:
        """Load a '.prompt' template file and runs it with the provided variables.

        :param prompt_path: path to the respective prompt file.
        :param variables: variables to passed to the LLM prompt template.
        :return: response from the LLM service.
        """
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        settings = PromptExecutionSettings(
            service_id=None
        )  # let SK choose default service

        # Call LLM
        result = await self.kernel.invoke_prompt(
            prompt=prompt_text, settings=settings, input_variables=variables
        )
        return str(result)
