# tests/test_multi_intent_flow.py

import json

import pytest
from config import Intent

from core.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_multi_intent_flow(monkeypatch, tmp_path):
    """
    Full multi-intent flow test using SK Plugins:
    - Initial email contains meter reading + product info request
    - Requires authentication (missing fields)
    - Authentication loop uses 2nd and 3rd emails
    - Intent handlers process the data via plugins
    - Aggregation plugin returns final merged email
    """

    # ----------------------------------
    # Create mock email structure
    # ----------------------------------
    conv_id = "multi_flow_test"
    conv_dir = tmp_path / "emails" / conv_id
    conv_dir.mkdir(parents=True)

    # Email 1 → two intents + missing auth info
    (conv_dir / "email_1.txt").write_text(
        """
        Hello LichtBlick Team,

        My meter number is LB-999000.
        My meter reading is 2000 kWh.
        Also, how does your dynamic tariff work?

        Regards, Julia
    """
    )

    # Email 2 → Partial auth data
    (conv_dir / "email_2.txt").write_text(
        """
        My installment amount is 50.
    """
    )

    # Email 3 → Full auth data
    (conv_dir / "email_3.txt").write_text(
        """
        My contract number is CN-123456.
        My full name is Julia Meyer.
    """
    )

    # Patch EMAIL_FOLDER so the orchestrator reads from our temp folder
    monkeypatch.setattr(
        "services.email_reader.EMAIL_FOLDER", str(tmp_path / "emails") + "/"
    )

    # ----------------------------------
    # Mock SK Plugin Calls via kernel.invoke()
    # ----------------------------------
    async def mock_invoke(self, plugin_name, func_name, args):

        # Intent detection → two intents detected
        if func_name == "detect_intents":
            return type(
                "Result",
                (object,),
                {"value": ["MeterReadingSubmission", "ProductInfoRequest"]},
            )()

        # Data extraction → behaves differently per email
        if func_name == "extract_data":
            email_text = args["email_text"].lower()

            # Email 1
            if "meter number" in email_text and "dynamic tariff" in email_text:
                return type(
                    "Result",
                    (object,),
                    {
                        "value": {
                            "meter_number": "LB-999000",
                            "meter_reading": 2000,
                            "tariff_questions": "How does your dynamic tariff work?",
                            "personal_data": {"full_name": "Julia"},
                        }
                    },
                )()

            # Email 2 (partial auth)
            if "installment" in email_text:
                return type(
                    "Result",
                    (object,),
                    {"value": {"personal_data": {"installment_amount": "50"}}},
                )()

            # Email 3 (full auth)
            if "contract number" in email_text:
                return type(
                    "Result",
                    (object,),
                    {
                        "value": {
                            "personal_data": {
                                "full_name": "Julia Meyer",
                                "contract_number": "CN-123456",
                                "installment_amount": "50",
                            }
                        }
                    },
                )()

        # Meter reading plugin
        if func_name == "save_meter_reading":
            return type(
                "Result",
                (object,),
                {
                    "value": {
                        "intent": "MeterReadingSubmission",
                        "status": "success",
                        "meter_number": args["meter_number"],
                        "meter_reading": args["meter_reading"],
                    }
                },
            )()

        # Product info plugin
        if func_name == "process_product_info_request":
            return type(
                "Result",
                (object,),
                {
                    "value": {
                        "intent": "ProductInfoRequest",
                        "status": "success",
                        "questions": args.get("tariff_questions"),
                    }
                },
            )()

        # Aggregation plugin returns final message
        if func_name == "aggregate_results":
            return type("Result", (object,), {"value": "FINAL MERGED EMAIL RESPONSE"})()

        # Default fallback for unhandled plugin calls
        return type("Result", (object,), {"value": {}})()

    # Patch kernel.invoke
    monkeypatch.setattr("semantic_kernel.Kernel.invoke", mock_invoke)

    # ----------------------------------
    # Mock Customer Database for authentication
    # ----------------------------------
    customer_db = {
        "test_customer": {
            "full_name": "Julia Meyer",
            "contract_number": "CN-123456",
            "installment_amount": "50",
        }
    }

    db_path = tmp_path / "mock_customer_db.json"
    db_path.write_text(json.dumps(customer_db))
    monkeypatch.setattr("config.MOCK_CUSTOMER_DB", str(db_path))

    # ----------------------------------
    # Run orchestrator
    # ----------------------------------
    orch = Orchestrator(conversation_id=conv_id)
    result = await orch.run()

    # ----------------------------------
    # Assertions
    # ----------------------------------
    assert "FINAL MERGED EMAIL RESPONSE" in result
