from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from ..config.config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_ENDPOINT
from ..plugins.aggregation_plugin import AggregationPlugin
from ..plugins.contract_plugin import ContractIssuesPlugin
from ..plugins.data_extraction_plugin import DataExtractionPlugin
from ..plugins.feedback_plugin import FeedbackPlugin
from ..plugins.intent_detection_plugin import IntentDetectionPlugin
from ..plugins.meter_reading_plugin import MeterReadingPlugin
from ..plugins.product_info_plugin import ProductInfoPlugin
from ..services.llm_service import LLMService


def build_kernel() -> Kernel:
    kernel = Kernel()

    kernel.add_service(
        AzureChatCompletion(
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        )
    )

    llm = LLMService(kernel)

    # Register plugins
    kernel.add_plugin(IntentDetectionPlugin(llm), "IntentDetectionPlugin")
    kernel.add_plugin(DataExtractionPlugin(llm), "DataExtractionPlugin")
    kernel.add_plugin(MeterReadingPlugin(), "MeterReadingPlugin")
    kernel.add_plugin(ProductInfoPlugin(), "ProductInfoPlugin")
    kernel.add_plugin(ContractIssuesPlugin(), "ContractIssuesPlugin")
    kernel.add_plugin(FeedbackPlugin(), "FeedbackPlugin")
    kernel.add_plugin(AggregationPlugin(llm), "AggregationPlugin")

    return kernel
