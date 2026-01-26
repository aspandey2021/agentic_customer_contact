from semantic_kernel.functions import kernel_function
from ..services.llm_service import LLMService


class AggregationPlugin:

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    @kernel_function(
        name="aggregate_results",
        description="Aggregates structured intent results into a customer-facing response email.",
    )
    async def aggregate_results(self, structured_json: str) -> str:

        reply = await self.llm.run_template(
            prompt_path="prompts/aggregation.prompt",
            variables={"structured_json": structured_json},
        )

        return reply
