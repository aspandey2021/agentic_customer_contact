"""Implement the config models."""

from enum import Enum


class Intent(str, Enum):
    """Enum class with members as the intents to be detected from customer email."""

    METER_READING = "MeterReadingSubmission"
    PERSONAL_DATA = "PersonalDataChange"
    CONTRACT_ISSUES = "ContractIssues"
    PRODUCT_INFO = "ProductInfoRequest"
    FEEDBACK = "GeneralFeedback"
