import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = "my-gpt-4o-mini"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"


HISTORY_FOLDER = "history/"


class Intent(str, Enum):
    METER_READING = "MeterReadingSubmission"
    PERSONAL_DATA = "PersonalDataChange"
    CONTRACT_ISSUES = "ContractIssues"
    PRODUCT_INFO = "ProductInfoRequest"
    FEEDBACK = "GeneralFeedback"
