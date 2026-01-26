import json
import logging
import os
from ..core.state import SharedState
from .email_reader import EmailReader
from ..plugins.data_extraction_plugin import DataExtractionPlugin
from ..core.sk_kernel import build_kernel
from .llm_service import LLMService
from .. import MOCK_CUSTOMER_DB

log = logging.getLogger(__name__)

class AuthenticationService:

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.customer_db = _load_mock_db()
        self.reader = EmailReader(conversation_id)

    def _find_customer_match(self, auth_data: dict) -> bool:
        """
        Checks if at least 3 fields match ANY customer.
        """
        for _, customer in self.customer_db.items():
            matches = 0

            for key, value in auth_data.items():
                if (
                    value
                    and key in customer
                    and str(customer[key]).lower() == str(value).lower()
                ):
                    matches += 1

            if matches >= 3:
                return True

        return False

    async def run_authentication_loop(self, state: SharedState):
        """
        Loop through sequential emails until authentication passes.
        """
        log.info("...Inside Authentication Loop...")

        email_index = 2  # initial request is 1, so next reply is email_2.txt

        while True:
            if self._find_customer_match(state.auth_data):
                log.info("***Authentication SUCCESS***")
                state.auth_validated = True
                return state

            log.warning("...Authentication FAILED or incomplete — requesting more info...")

            # Load next mock email reply
            try:
                next_email = self.reader.load_email(email_index)
                email_index += 1
            except FileNotFoundError:
                raise RuntimeError(
                    f"Authentication could not be completed — ran out of mock reply emails.\n"
                    f"Last attempted email index: {email_index}"
                )

            # Add that email to the history
            state.add_history(role="customer", content=next_email)

            # Extract personal data (reuse extraction agent!)
            kernel = build_kernel()
            extractor = DataExtractionPlugin(LLMService(kernel))

            extracted = await extractor.extract_data(next_email)

            personal = extracted.get("personal_data", {})

            # Merge new personal data into state
            for k, v in personal.items():
                if v:
                    state.auth_data[k] = v

            print("Current auth_data:", state.auth_data)


def _load_mock_db():
    if not os.path.exists(MOCK_CUSTOMER_DB):
        raise FileNotFoundError("mock_customer_db.json missing.")

    with open(MOCK_CUSTOMER_DB, "r", encoding="utf-8") as f:
        return json.load(f)