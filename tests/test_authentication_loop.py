import json

import pytest
from state import SharedState

from services.auth_service import AuthenticationService


@pytest.mark.asyncio
async def test_auth_loop(monkeypatch, tmp_path):
    # Mock customer DB
    customer_db = {
        "cust1": {
            "full_name": "Julia Meyer",
            "contract_number": "CN-556677",
            "installment_amount": "50",
        }
    }

    db_path = tmp_path / "mock_customer_db.json"
    db_path.write_text(json.dumps(customer_db))
    monkeypatch.setattr("config.MOCK_CUSTOMER_DB", str(db_path))

    # Email replies
    email_dir = tmp_path / "emails" / "conv"
    email_dir.mkdir(parents=True)

    (email_dir / "email_1.txt").write_text("Hi, I am Julia Meyer.")
    (email_dir / "email_2.txt").write_text("Installment is 50.")
    (email_dir / "email_3.txt").write_text("Contract number is CN-556677.")

    monkeypatch.setattr(
        "services.auth_service.EmailReader.load_email",
        lambda self, i: (email_dir / f"email_{i}.txt").read_text(),
    )

    # Mock extraction plugin
    async def mock_extract(kernel, plugin, function, args):
        text = args["email_text"].lower()
        if "contract number" in text:
            return {"personal_data": customer_db["cust1"]}
        elif "installment" in text:
            return {"personal_data": {"installment_amount": "50"}}
        else:
            return {"personal_data": {"full_name": "Julia Meyer"}}

    monkeypatch.setattr(
        "services.auth_service.AuthenticationService._extract_personal_data",
        mock_extract,
        raising=False,
    )

    state = SharedState(conversation_id="conv")
    state.add_history("customer", "Hi")

    auth = AuthenticationService("conv")

    # Replace extraction call
    monkeypatch.setattr(
        "agents.data_extraction_plugin.DataExtractionPlugin.extract_data",
        lambda self, email_text: mock_extract(
            None, None, None, {"email_text": email_text}
        ),
    )

    state = await auth.run_authentication_loop(state)

    assert state.auth_validated is True
