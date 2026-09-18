from .classifier import SYSTEM_PROMPT, parse_classification
from .classification import Classification
from .llm_client import LLMClient, LLMProviderError


class LLMClassifier:
    def __init__(self, client=None):
        self.client = client or LLMClient()

    def classify(self, ticket_text: str):
        for attempt in range(2):
            try:
                response = self.client.complete(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=ticket_text,
                )
            except LLMProviderError:
                raise

            try:
                return parse_classification(response)
            except (ValueError, TypeError):
                if attempt == 1:
                    return Classification(
                        intent="unclear_request",
                        urgency="medium",
                        confidence=0.0,
                    )

        raise RuntimeError("Classification failed unexpectedly.")
