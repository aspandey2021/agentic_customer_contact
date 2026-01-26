from pathlib import Path

PR_ROOT = Path(__file__).parent.parent
DATA_ROOT = PR_ROOT / "data"
EMAIL_ROOT = DATA_ROOT / "emails"
HISTORY_ROOT = PR_ROOT / "history"

PROMPT_ROOT = PR_ROOT / "prompts"
INTENT_DETECTION_PROMPT = PROMPT_ROOT / "intent_detection.prompt"
DATA_EXTRACTION_PROMPT = PROMPT_ROOT / "data_extraction.prompt"
AGGREGATION_PROMPT = PROMPT_ROOT / "aggregation.prompt"

MOCK_CUSTOMER_DB = "data/mock_customer_db.json"
MOCK_METER_DB = "data/mock_meter_db.json"