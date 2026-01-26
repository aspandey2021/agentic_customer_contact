from pathlib import Path
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import PromptExecutionSettings
from typing import Any


class LLMService:
    """
    Wrapper around Semantic Kernel to load prompt templates,
    inject variables, and call Azure OpenAI via Semantic Kernel.
    """

    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def run_template(self, prompt_path: Path | str, variables: dict[str, Any]) -> str:
        """
        Loads a '.prompt' template file and runs it with the provided variables.
        """
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()

        # Prepare settings (Azure Chat Completion)
        settings = PromptExecutionSettings(
            service_id=None
        )  # let SK choose default service

        # Call LLM
        result = await self.kernel.invoke_prompt(prompt=prompt_text,settings=settings, input_variables=variables)

        return str(result)
