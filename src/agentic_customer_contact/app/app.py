"""Entrypoint to the agentic customer contact application."""

import asyncio
import logging

from agentic_customer_contact.core.orchestrator import Orchestrator

log = logging.getLogger(__name__)


def main() -> None:
    """Run the agentic ai entrypoint."""
    conversation_id = "first"

    orch = Orchestrator(conversation_id, email_id=1)
    final_email = asyncio.run(orch.run())

    log.info(f"Final Email Reply :\n{final_email}")


if __name__ == "__main__":
    main()
