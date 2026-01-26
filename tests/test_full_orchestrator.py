import json

import pytest
from config import Intent

from core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_full_orchestrator(monkeypatch, tmp_path):
    # Fake conversation folder
    conv_id = "full_test"
    email_dir = tmp_path / "emails" / conv_id
    email_dir.mkdir(parents=True)

    (email_dir / "email_1.txt").write_text(
        """
        My meter reading is 2000 kWh.
        My meter number is LB-9876543.
        Also, how does your dynamic tariff work?
        Regards, Julia
    """
    )

    (email_dir / "email_2.txt").write_text(
        """
        Contract number: CN-556677
        Installment amount: 50
        Name: Julia Meyer
    """
    )

    # Monkeypatch EMAIL_FOLDER
    monkeypatch.setattr(
        "services.email_reader.EMAIL_FOLDER", str(tmp_path / "emails") + "/"
    )

    # Mock SK plugin calls
    async def mock_invoke(self, plugin, function, args):
        if function == "detect_intents":
            return type(
                "Result",
                (object,),
                {"value": ["MeterReadingSubmission", "ProductInfoRequest"]},
            )()
        if function == "extract_data":
            return type(
                "Result",
                (object,),
                {
                    "value": {
                        "meter_reading": 2000,
                        "meter_number": "LB-9876543",
                        "tariff_questions": "How does your dynamic tariff work?",
                        "personal_data": {"full_name": "Julia"},
                    }
                },
            )()
        if function == "save_meter_reading":
            return type("Result", (object,), {"value": {"status": "success"}})()
        if function == "process_product_info_request":
            return type("Result", (object,), {"value": {"status": "success"}})()
        if function == "aggregate_results":
            return type("Result", (object,), {"value": "FINAL EMAIL"})()
        return type("Result", (object,), {"value": {}})()

    monkeypatch.setattr("semantic_kernel.Kernel.invoke", mock_invoke)

    orch = Orchestrator(conv_id)
    result = await orch.run()

    assert "FINAL EMAIL" in result
