# plugins/feedback_plugin.py

from semantic_kernel.functions import kernel_function


class FeedbackPlugin:

    @kernel_function(
        name="process_feedback",
        description="Processes general customer feedback in structured form.",
    )
    async def process_feedback(self, feedback_text: str | None) -> dict:

        return {
            "intent": "GeneralFeedback",
            "status": "success",
            "feedback": feedback_text,
        }
