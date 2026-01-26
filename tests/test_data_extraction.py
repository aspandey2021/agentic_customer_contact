import pytest
from semantic_kernel import Kernel

from plugins.data_extraction_plugin import DataExtractionPlugin
from services.llm_service import LLMService


@pytest.mark.asyncio
async def test_data_extraction(monkeypatch):
    kernel = Kernel()
    llm = LLMService(kernel)

    plugin = DataExtractionPlugin(llm)

    async def mock_run_template(self, path, variables):
        return '{"meter_reading": 2000, "meter_number": "LB-12345"}'

    monkeypatch.setattr(LLMService, "run_template", mock_run_template)

    data = await plugin.extract_data("Some email text")
    assert data["meter_reading"] == 2000
    assert data["meter_number"] == "LB-12345"
