"""Implement the meter reading Plugin."""

import json
import os
from datetime import datetime

from semantic_kernel.functions import kernel_function

from .. import MOCK_METER_DB


class MeterReadingPlugin:
    """Class for plugin to save the meter reading to a given DB."""

    def __init__(self) -> None:
        """Initialise the DB."""
        if os.path.exists(MOCK_METER_DB):
            try:
                with open(MOCK_METER_DB, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
            except FileNotFoundError:
                self.db = {}
        else:
            self.db = {}

    def _save_db(self):
        """Save the meter readings to the DB."""
        os.makedirs(os.path.dirname(MOCK_METER_DB), exist_ok=True)
        with open(MOCK_METER_DB, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=2)

    @kernel_function(
        name="save_meter_reading",
        description="Saves a validated meter reading to the mock meter DB.",
    )
    async def save_meter_reading(
        self, meter_number: str, meter_reading: float, conversation_id: str
    ) -> dict:
        """Built the save meter reading plugin function.

        :param meter_number: extracted meter number from the email.
        :param meter_reading: extracted meter reading from the email.
        :param conversation_id: str identifier for the current conversation thread.
        :return: dict containing values saved to the DB with status and timestamp.
        """
        timestamp = datetime.now().isoformat()
        self.db[meter_number] = {
            "reading": meter_reading,
            "timestamp": timestamp,
            "conversation_id": conversation_id,
        }
        self._save_db()

        return {
            "saved": True,
            "meter_number": meter_number,
            "meter_reading": meter_reading,
            "timestamp": timestamp,
        }
