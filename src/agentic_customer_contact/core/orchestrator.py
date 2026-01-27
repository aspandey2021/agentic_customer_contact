"""Implement the orchestrator of the agentic system."""

import asyncio
import json
import logging

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments

from ..config.config import Intent
from ..services.auth_service import AuthenticationService
from ..services.email_reader import EmailReader
from ..services.email_writer import EmailWriter
from .history import ConversationHistory
from .intent_handler import HandlerOfIntents
from .sk_kernel import build_kernel
from .state import SharedState

log = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrator Class for orchestrating the entire agentic system."""

    def __init__(
        self, conversation_id: str = "default_conversation", email_id: int = 1
    ) -> None:
        """Initialize the Orchestrator Class.

        :param conversation_id: str identifier for the current conversation thread.
        :param email_id: int index of the email to be read at the start.
        """
        self.conversation_id = conversation_id
        self.reader = EmailReader(conversation_id)
        self.writer = EmailWriter(conversation_id)
        self.kernel = build_kernel()
        self.intents_req_auth = [
            Intent.METER_READING,
            Intent.PERSONAL_DATA,
            Intent.CONTRACT_ISSUES,
        ]

        # Authentication will use SK extraction plugin, but loop logic stays external
        self.auth_service = AuthenticationService(self.conversation_id, self.kernel)
        self.starting_email_id = email_id
        self.next_email_id = self.starting_email_id + 1

        # Event used for signalling that authentication is complete
        self.auth_completed = asyncio.Event()
        self.handler = HandlerOfIntents(
            kernel=self.kernel, conversation_id=self.conversation_id
        )

    async def run(self) -> str:
        """Run the orchestrator."""
        log.info("===Starting Agentic Workflow (Semantic Kernel Plugins Enabled)===")

        log.info("...Reading Emails and Initialising Shared State and History...")
        email_text = self.reader.load_email(self.starting_email_id)
        state = self._initialise_state(email_text=email_text)

        log.info("...Detecting intents...")
        state.intents = await self._detect_intents(
            email_text=email_text
        )  # state.intents contains: ["MeterReadingSubmission",...]
        log.info(f"... Detected intents are : {state.intents}")

        log.info("...Extracting data...")
        extracted_data = await self._extract_data(email_text=email_text)
        state.extracted_data = extracted_data
        log.info("...Extracted data : ", json.dumps(extracted_data, indent=2))

        to_auth_intents = [
            intent for intent in state.intents if intent in self.intents_req_auth
        ]
        no_auth_intents = [
            intent for intent in state.intents if intent not in self.intents_req_auth
        ]
        log.info(f"Intents requiring authentication are: {to_auth_intents}")

        auth_task = None
        if to_auth_intents:
            state.auth_data.update(extracted_data.get("personal_data", {}))
            auth_task = asyncio.create_task(
                self._authenticate_and_signal(state, self.next_email_id)
            )
        else:
            self.auth_completed.set()

        log.info("...Handling intents via SK Plugins...")
        no_auth_tasks = []
        for intent in no_auth_intents:
            t = asyncio.create_task(
                self._intent_handler(intent, state, extracted_data, requires_auth=False)
            )
            no_auth_tasks.append(t)

        auth_tasks = []
        for intent in to_auth_intents:
            t = asyncio.create_task(
                self._intent_handler(intent, state, extracted_data, requires_auth=True)
            )
            auth_tasks.append(t)

        all_tasks = no_auth_tasks + auth_tasks
        if auth_task:
            await auth_task

        results: [dict] = await asyncio.gather(*all_tasks)
        intent_outputs = {intent.value: result for intent, result in results}
        log.info(f"Intent outputs combined : {json.dumps(intent_outputs, indent=2)}")

        log.info("...Aggregating final customer email via SK plugin...")
        aggregated_reply = await self._aggregate(intent_output=intent_outputs)

        final_reply = (
            aggregated_reply.value
            if hasattr(aggregated_reply, "value")
            else str(aggregated_reply)
        )

        # Save to history
        state.add_history("assistant", final_reply)
        conv_history = ConversationHistory(self.conversation_id)
        conv_history.save(state.history)

        self.writer.write_response(final_reply, index=1)

        log.info("===Agentic Workflow Complete===")
        return final_reply

    async def _aggregate(self, intent_output: dict) -> FunctionResult:
        """Aggregate the results from all plugins and consolidate it into an LLM Reply.

        :param intent_output: dict containing all outputs from the plugins.
        :return: A FunctionResult object containing the consolidated and LLM generated reply.
        """
        aggregated_reply = await self.kernel.invoke(
            plugin_name="AggregationPlugin",
            function_name="aggregate_results",
            arguments=KernelArguments(structured_json=json.dumps(intent_output)),
        )
        return aggregated_reply

    async def _authenticate_and_signal(
        self, state: SharedState, next_email_id: int = 2
    ) -> None:
        """Runs authentication ONCE and signals the waiting intent tasks.

        :param state: current shared state, which has parameters like if auth_validated True or False, etc.
        :param next_email_id: index of the next conversation email to be read.
        :return: None.
        """
        updated_state = await self.auth_service.run_authentication_loop(
            state, next_email_id
        )

        state.auth_validated = updated_state.auth_validated
        state.auth_data = updated_state.auth_data
        # Signal ALL waiting tasks
        self.auth_completed.set()

    async def _detect_intents(self, email_text: str) -> [Intent]:
        """Detect the intents contained in the customer email using an intent detection plugin.

        :param email_text: content of the customer email.
        :return: List of intents as members of dataclass Intent.
        """
        intents_raw = await self.kernel.invoke(
            plugin_name="IntentDetectionPlugin",
            function_name="detect_intents",
            arguments=KernelArguments(email_text=email_text),
        )
        # SK returns an SKResult → extract text/value
        intents_list = (
            intents_raw.value if hasattr(intents_raw, "value") else intents_raw
        )
        return [Intent(i) for i in intents_list]

    async def _extract_data(self, email_text: str) -> dict:
        """Extract the relevant customer data from email, like name, address etc. using an extraction plugin.

        :param email_text: string content of the customer email.
        :return: dict containing relevant extracted parameters.
        """
        extracted_raw = await self.kernel.invoke(
            plugin_name="DataExtractionPlugin",
            function_name="extract_data",
            arguments=KernelArguments(email_text=email_text),
        )
        extracted_data = (
            extracted_raw.value if hasattr(extracted_raw, "value") else extracted_raw
        )
        return extracted_data

    def _initialise_state(self, email_text: str) -> SharedState:
        """Initialise the shared state and its parameters.

        :param email_text: content of the customer email.
        :return: Updated shared state.
        """
        state = SharedState(conversation_id=self.conversation_id)
        state.email_text = email_text
        state.add_history("customer", email_text)
        return state

    async def _intent_handler(
        self,
        intent: Intent,
        state: SharedState,
        extracted: dict,
        requires_auth: bool = True,
    ) -> [Intent, dict]:
        """Executes an intent handler with optional authentication wait.

        :param intent: str, Intent which needs to be handled.
        :param state: Current shared State.
        :param extracted: extracted customer data from email, like meter reading, personal data etc.
        :param requires_auth: boolean, if the intent requires authentication or not.
        :return: corresponding intent and a dict of values handled by the respective plugin.
        """
        if requires_auth:
            log.info(f"Waiting for authentication for {intent}...")
            await self.auth_completed.wait()
            log.info(f"{intent} Authentication complete, running handler...")

        if intent == Intent.METER_READING:
            # return await self._handle_meter_reading(intent, extracted)
            return await self.handler.handle_meter_reading(intent, extracted)
        elif intent == Intent.PRODUCT_INFO:
            # return await self._handle_product_info(intent, extracted)
            return await self.handler.handle_product_info(intent, extracted)

        return intent, {"status": "ignored"}
