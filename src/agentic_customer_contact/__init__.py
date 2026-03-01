import os
from pathlib import Path

from dotenv import load_dotenv

PR_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = PR_ROOT / "data"
EMAIL_FOLDER = DATA_ROOT / "emails"
HISTORY_FOLDER = PR_ROOT / "history"

PROMPT_ROOT = PR_ROOT / "prompts"
INTENT_DETECTION_PROMPT = PROMPT_ROOT / "intent_detection.prompt"
DATA_EXTRACTION_PROMPT = PROMPT_ROOT / "data_extraction.prompt"
AGGREGATION_PROMPT = PROMPT_ROOT / "aggregation.prompt"
PRODUCT_INFO_PROMPT = PROMPT_ROOT / "product_info.prompt"

MOCK_CUSTOMER_DB = DATA_ROOT / "mock_customer_db.json"
MOCK_METER_DB = DATA_ROOT / "mock_meter_db.json"

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "my-gpt-4o-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
