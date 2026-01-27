"""Implement the aggregation Plugin."""

from pathlib import Path

from semantic_kernel.functions import kernel_function

from ..services.llm_service import LLMService


class AggregationPlugin:
    """Class to aggregate the results from all plugins and consolidate it into an LLM Reply."""

    def __init__(self, llm_service: LLMService, prompt_path: Path | str) -> None:
        """Initialise.

        :param llm_service: corresponding Azure service bound to the build kernel.
        :param prompt_path: Path to the aggregation prompt file.
        """
        self.llm = llm_service
        self.prompt_path = prompt_path

    @kernel_function(
        name="aggregate_results",
        description="Aggregates structured intent results into a customer-facing response email.",
    )
    async def aggregate_results(self, structured_json: str) -> str:
        """Built the aggregate plugin function.

        :param structured_json: json formatted string containing all outputs from the plugins.
        :return: LLM generated reply.
        """
        reply = await self.llm.run_template(
            prompt_path=self.prompt_path,
            variables={"structured_json": structured_json},
        )

        return reply
