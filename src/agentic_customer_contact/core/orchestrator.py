import asyncio
import json
import logging
from typing import Dict
from ..config.config import Intent
from .sk_kernel import build_kernel
from .state import SharedState

from .history import ConversationHistory
from ..services.auth_service import AuthenticationService
from ..services.email_reader import EmailReader
from ..services.email_writer import EmailWriter

log = logging.getLogger(__name__)

class Orchestrator:

    def __init__(self, conversation_id: str = "default_conversation", email_id: int=0) -> None:
        self.conversation_id = conversation_id
        self.reader = EmailReader(conversation_id)
        self.writer = EmailWriter(conversation_id)
        self.kernel = build_kernel()
        self.intents_req_auth = [Intent.METER_READING,Intent.PERSONAL_DATA,Intent.CONTRACT_ISSUES]

        # Authentication will use SK extraction plugin, but loop logic stays external
        self.auth_service = AuthenticationService(conversation_id)
        self.email_id = email_id

        # Event used for signalling that authentication is complete
        self.auth_completed = asyncio.Event()


    async def run(self) -> str:
        log.info("===Starting Agentic Workflow (Semantic Kernel Plugins Enabled)===")

        log.info("...Reading Emails and Initialising Shared State and History...")
        email_text = self.reader.load_email(self.email_id)
        state = self._initialise_state(email_text=email_text)

        log.info("...Detecting intents...")
        state.intents = self._detect_intents(email_text=email_text) # state.intents: ["MeterReadingSubmission",...]
        log.info(f"... Detected intents are : {state.intents}")

        log.info("...Extracting data...")
        extracted_data = self._extract_data(email_text=email_text)
        state.extracted_data = extracted_data
        log.info("... Extracted data : ", json.dumps(extracted_data, indent=2))

        to_auth_intents = [intent for intent in state.intents if intent in self.intents_req_auth]
        no_auth_intents = [intent for intent in state.intents if intent not in self.intents_req_auth]
        log.info(f"Intents requiring authentication are: {to_auth_intents}")

        auth_task = None
        if to_auth_intents:
            state.auth_data.update(extracted_data.get("personal_data", {}))
            auth_task = asyncio.create_task(self._authenticate_and_signal(state))
        else:
            self.auth_completed.set()

        # if any(i.value in state.intents for i in intents_requiring_auth):
        #     log.info("...Authentication required — starting authentication loop...")
        #
        #     state.auth_data.update(extracted_data.get("personal_data", {}))
        #
        #     state = await self.auth_service.run_authentication_loop(state)
        # else:
        #     log.info("...No authentication required...")

        log.info("...Handling intents via SK Plugins...")
        no_auth_tasks = []
        for intent in no_auth_intents:
            t = asyncio.create_task(self._intent_handler(intent, state, extracted_data, requires_auth=False))
            no_auth_tasks.append(t)

        auth_tasks = []
        for intent in to_auth_intents:
            t = asyncio.create_task(self._intent_handler(intent, state, extracted_data, requires_auth=True))
            auth_tasks.append(t)

        all_tasks = no_auth_tasks + auth_tasks
        if auth_task:
            await auth_task

        results: [dict] = await asyncio.gather(*all_tasks)
        intent_outputs = {intent.value: result for intent, result in results}
        email_text_full = email_text
        log.info(f"Intent outputs combined : {json.dumps(intent_outputs, indent=2)}")

        for intent in state.intents:
            # intent = "MeterReadingSubmission" e.g.
            # ------------------------------
            # Meter Reading
            # ------------------------------
            if intent == Intent.METER_READING:
                meter_num = extracted_data.get("meter_number")
                meter_reading = extracted_data.get("meter_reading")

                if not meter_num or not meter_reading:
                    raise ValueError("MeterReadingSubmission missing required fields.")

                result = await self.kernel.invoke(
                    plugin_name="MeterReadingPlugin",
                    function_name="save_meter_reading",
                    arguments={
                        "meter_number": meter_num,
                        "meter_reading": meter_reading,
                        "conversation_id": self.conversation_id,
                    },
                )
                intent_outputs[intent] = result.value

            # ------------------------------
            # Product Info
            # ------------------------------
            elif intent == Intent.PRODUCT_INFO:
                questions = extracted_data.get("tariff_questions")

                result = await self.kernel.invoke(
                    plugin_name="ProductInfoPlugin",
                    function_name="process_product_info_request",
                    arguments={"tariff_questions": questions},
                )

                intent_outputs[intent.value] = result.value


        log.info("...Intent outputs ready : ", json.dumps(intent_outputs, indent=2))

        # -------------------------------------------------
        # STEP 6 — Aggregation (SK Plugin -> LLM)
        # -------------------------------------------------
        log.info("...Aggregating final customer email via SK plugin...")

        final_reply_raw = await self.kernel.invoke(
            plugin_name="AggregationPlugin",
            function_name="aggregate_results",
            arguments={"structured_json": json.dumps(intent_outputs)},
        )

        final_reply = (
            final_reply_raw.value
            if hasattr(final_reply_raw, "value")
            else str(final_reply_raw)
        )

        # Save to history
        state.add_history("assistant", final_reply)
        ConversationHistory.save(self.conversation_id, state.history)

        # -------------------------------------------------
        # STEP 7 — Save assistant reply as mock email
        # -------------------------------------------------
        self.writer.write_response(final_reply, index=1)

        print("\n=== Agentic Workflow Complete ===")
        return final_reply


    def _authenticate_and_signal(self, state: SharedState) -> None:
        """Runs authentication ONCE and signals the waiting intent tasks."""
        updated_state = await self.auth_service.run_authentication_loop(state)

        state.auth_validated = updated_state.auth_validated
        state.auth_data = updated_state.auth_data
        # Signal ALL waiting tasks
        self.auth_completed.set()
    def _detect_intents(self, email_text: str) -> [Intent]:
        intents_raw = await self.kernel.invoke(plugin_name="IntentDetectionPlugin", function_name="detect_intents",
                                               arguments={"email_text": email_text})

        # SK returns an SKResult → extract text/value
        intents_list = (
            intents_raw.value if hasattr(intents_raw, "value") else intents_raw
        )
        return [Intent(i) for i in intents_list]

    def _extract_data(self, email_text: str) -> dict:
        extracted_raw = await self.kernel.invoke(
            plugin_name="DataExtractionPlugin", function_name="extract_data", arguments={"email_text": email_text}
        )
        extracted_data = (
            extracted_raw.value if hasattr(extracted_raw, "value") else extracted_raw
        )
        return extracted_data

    def _initialise_state(self, email_text: str) -> SharedState:
        state = SharedState(conversation_id=self.conversation_id)
        state.email_text = email_text
        state.add_history("customer", email_text)
        return state

    def _intent_handler(self, intent, state, extracted, requires_auth: bool = True):
        """Executes an intent handler with optional authentication wait."""
        if requires_auth:
            log.info(f"Waiting for authentication for {intent}...")
            await self.auth_completed.wait()
            log.info(f"{intent} Authentication complete, running handler...")



    # extracted_data
    # {
    #   "meter_reading": 2438,
    #   "meter_number": "LB-9876543",
    #   "reading_date": "25.09.2025",
    #   "personal_data": {
    #     "full_name": "Julia Meyer",
    #     "address": null,
    #     "contract_number": null,
    #     "birthday": null,
    #     "installment_amount": null,
    #     "customer_number": null
    #   },
    #   "tariff_questions": "The customer asks how the dynamic tariff works, whether it makes sense for a 2-person household with an induction stove and no EV, whether prices change hourly, and if switching is possible at any time.",
    #   "feedback": null
    # }