import asyncio

from ..core.orchestrator import Orchestrator

def main():
    conversation_id = "example_conversation"

    orch = Orchestrator(conversation_id)
    final_email = asyncio.run(orch.run())

    print("\nFinal Email Reply:\n")
    print(final_email)


if __name__ == "__main__":
    main()
