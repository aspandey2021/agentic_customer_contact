**Agentic Customer Contact Copilot (Semantic Kernel + Azure OpenAI)**

This project implements the full Agentic Customer Contact Copilot case study from LichtBlick SE using:

Python 3.11.14

Semantic Kernel = 1.10.1

Azure OpenAI (GPT-4o-mini)

SK Plugin Architecture (kernel functions)

Agentic Orchestration

Authentication loop using mock emails

Deterministic test suite (pytest)

All external systems (email inbox, backend systems, authentication) are mocked so the entire project works locally without Azure during tests.
Real Azure OpenAI calls occur only in production mode.

**Features**:

SK Plugin Architecture

Each agent is implemented as an SK Plugin via @kernel_function:

IntentDetectionPlugin

DataExtractionPlugin

MeterReadingPlugin

ProductInfoPlugin

ContractIssuesPlugin

FeedbackPlugin

AggregationPlugin

**Multi-Turn Simulation**

Emails will be stored as:

data/emails/case_example/email_1.txt
data/emails/case_example/email_2.txt
data/emails/case_example/email_3.txt
...

**Modular & Testable**

All plugins are pure SK functions

Orchestrator uses kernel.invoke() for every action

LLM calls mocked during pytest

**Azure Integration**

Uses Azure OpenAI deployment:

AZURE_OPENAI_ENDPOINT

AZURE_OPENAI_API_KEY

AZURE_OPENAI_DEPLOYMENT

**Installation**

Creating a virtual environment:

python -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt

**Set environment variables:**

create a .env file and store the Azure Endpoint and credentials as :

AZURE_OPENAI_ENDPOINT="https://<your-instance>.openai.azure.com"
AZURE_OPENAI_API_KEY="<your-api-key>"
AZURE_OPENAI_DEPLOYMENT="deployment-name"

**Running the App**

python -m agentic_customer_contact/app/app.py

**Running Tests**

python -m pytest tests/test_orchestrator.py 


All tests run without Azure access, because SK plugin calls get monkeypatched.

Have a good day!