import pytest
from semantic_kernel import Kernel

from plugins.intent_detection_plugin import IntentDetectionPlugin
from services.llm_service import LLMService


@pytest.mark.asyncio
async def test_intent_detection(monkeypatch):
    kernel = Kernel()
    llm = LLMService(kernel)

    plugin = IntentDetectionPlugin(llm)

    async def mock_run_template(self, prompt_path, variables):
        return '["MeterReadingSubmission", "ProductInfoRequest"]'

    monkeypatch.setattr(LLMService, "run_template", mock_run_template)

    result = await plugin.detect_intents("test email")
    assert "MeterReadingSubmission" in result
    assert "ProductInfoRequest" in result
