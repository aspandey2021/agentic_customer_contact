from unittest.mock import AsyncMock, MagicMock

import pytest

from agentic_customer_contact.config.config import Intent
from agentic_customer_contact.core.orchestrator import Orchestrator
from agentic_customer_contact.core.state import SharedState

pytestmark = pytest.mark.asyncio

EMAIL_METER_SUBMISSION = """
Hello XYZ AG Team,
My new meter reading is 54321 for meter number 876543.
Best regards,
Alice
"""

EMAIL_PRODUCT_INFO = """
Hi,
I would like to know more about your green electricity tariffs.
Thanks,
Bob
"""

EMAIL_REPLY_AUTH = """
Hi,
Here is my customer number: 123456 and my postal code 22299.
"""


class MockKernelInvoke:
    def __init__(self, value):
        self.value = value


class TestOrchestrator:
    def setup_method(self) -> None:
        orch = Orchestrator(conversation_id="test_conversation", email_id=1)

        # Mock reader + writer
        orch.reader = MagicMock()
        orch.writer = MagicMock()

        # Mock build_kernel() inside orchestrator
        orch.kernel = MagicMock()
        orch.kernel.invoke = AsyncMock()

        # Authentication service is mocked completely
        orch.auth_service = MagicMock()
        orch.auth_service.run_authentication_loop = AsyncMock()

        orch.handler = MagicMock()
        orch.handler.handle_meter_reading = AsyncMock()
        orch.handler.handle_product_info = AsyncMock()
        self.orch = orch

    async def test__runs_with_single_intent_no_auth(self):

        final_reply = "Final Reply"
        self.orch.reader.load_email.return_value = EMAIL_PRODUCT_INFO
        self.orch.kernel.invoke.side_effect = [
            MockKernelInvoke([Intent.PRODUCT_INFO]),
            MockKernelInvoke({"tariff_questions": "Tell me about tariffs"}),
            MockKernelInvoke(final_reply),
        ]
        self.orch.handler.handle_product_info.return_value = (
            Intent.PRODUCT_INFO,
            {"info": "tariff details"},
        )
        actual_reply = await self.orch.run()

        assert actual_reply == final_reply
        self.orch.writer.write_response.assert_called_once()
        assert self.orch.kernel.invoke.call_count == 3
        # Ensure product info plugin was invoked
        self.orch.handler.handle_product_info.assert_awaited_once()

    async def test__runs_with_single_intent_with_auth(self):
        final_reply = "Final Reply"
        self.orch.reader.load_email.return_value = [
            EMAIL_METER_SUBMISSION,
            EMAIL_REPLY_AUTH,
        ]
        self.orch.kernel.invoke.side_effect = [
            MockKernelInvoke([Intent.METER_READING]),
            MockKernelInvoke(
                {
                    "meter_number": "876543",
                    "meter_reading": "54321",
                    "personal_data": {},
                }
            ),
            MockKernelInvoke(final_reply),
        ]
        self.orch.handler.handle_meter_reading.return_value = (
            Intent.METER_READING,
            {"saved": True},
        )
        self.orch.auth_service.run_authentication_loop.return_value = SharedState(
            conversation_id="test_conv",
            auth_validated=True,
            auth_data={"customer_id": "123456"},
        )
        actual_reply = await self.orch.run()

        assert actual_reply == final_reply
        self.orch.writer.write_response.assert_called_once()
        assert self.orch.kernel.invoke.call_count == 3
        # Ensure meter reading plugin was invoked
        self.orch.handler.handle_meter_reading.assert_awaited_once()

    async def test__runs_with_mixed_intents_auth_and_no_auth(self):
        final_reply = "Final Reply"
        self.orch.reader.load_email.return_value = [
            EMAIL_METER_SUBMISSION + EMAIL_PRODUCT_INFO,
            EMAIL_REPLY_AUTH,
        ]
        self.orch.kernel.invoke.side_effect = [
            MockKernelInvoke([Intent.METER_READING, Intent.PRODUCT_INFO]),
            MockKernelInvoke(
                {
                    "meter_number": "876543",
                    "meter_reading": "54321",
                    "personal_data": {},
                    "tariff_questions": "Tell me about tariffs",
                }
            ),
            MockKernelInvoke(final_reply),
        ]
        self.orch.auth_service.run_authentication_loop.return_value = SharedState(
            conversation_id="test_conv",
            auth_validated=True,
            auth_data={"customer_id": "123456"},
        )
        self.orch.handler.handle_product_info.return_value = (
            Intent.PRODUCT_INFO,
            {"info": "tariff details"},
        )
        self.orch.handler.handle_meter_reading.return_value = (
            Intent.METER_READING,
            {"saved": True},
        )

        actual_reply = await self.orch.run()

        assert actual_reply == final_reply
        self.orch.writer.write_response.assert_called_once()
        assert self.orch.kernel.invoke.call_count == 3
        # Ensure meter reading and product info plugins were invoked
        self.orch.handler.handle_product_info.assert_awaited_once()
        self.orch.handler.handle_meter_reading.assert_awaited_once()
