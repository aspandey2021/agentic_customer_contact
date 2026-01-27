"""Implement the authentication service class."""
import json
import logging
import os

from semantic_kernel import Kernel
from semantic_kernel.functions.kernel_arguments import KernelArguments

from .. import MOCK_CUSTOMER_DB
from ..core.state import SharedState
from .email_reader import EmailReader

log = logging.getLogger(__name__)


class AuthenticationService:
    """Class to carry out authentication service, for intents requiring authentication."""
    def __init__(self, conversation_id: str, kernel: Kernel):
        """Initialise.

        :param conversation_id: str identifier for the current conversation thread.
        :param kernel: Kernel object containing relevant Azure Services and plugins.
        """
        self.conversation_id = conversation_id
        self.kernel = kernel
        self.customer_db = _load_mock_db()
        self.reader = EmailReader(conversation_id)

    def _find_customer_match(self, auth_data: dict) -> bool:
        """Check if at least 3 fields match ANY customer.

        :param auth_data: extracted personal data of customer to be used for authorization.
        :return: boolean, if authorized or not.
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

    async def run_authentication_loop(
        self, state: SharedState, email_id: int
    ) -> SharedState:
        """Loop through sequential emails until authentication passes.

        :param state: current shared state, which has parameters like conversation_id, email_text etc.
        :param email_id: int index of the email to be read for authentication.
        :return: updated current shared state.
        """
        log.info("...Inside Authentication Loop...")
        email_index = email_id  # if initial request is 1, so next reply is email_2.txt

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

            extracted_raw = await self.kernel.invoke(
                plugin_name="DataExtractionPlugin",
                function_name="extract_data",
                arguments=KernelArguments(email_text=next_email),
            )
            extracted = extracted_raw.value
            personal = extracted.get("personal_data", {})

            # Merge new personal data into state
            for k, v in personal.items():
                if v:
                    state.auth_data[k] = v

            log.info("Current auth_data:", state.auth_data)


def _load_mock_db():
    """Load mock customer DB for authentication."""
    if not os.path.exists(MOCK_CUSTOMER_DB):
        raise FileNotFoundError("mock_customer_db.json missing.")

    with open(MOCK_CUSTOMER_DB, "r", encoding="utf-8") as f:
        return json.load(f)
