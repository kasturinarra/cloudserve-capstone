from dataclasses import dataclass

from .classification import Classification
from .llm_classifier import LLMClassifier
from .routing import RoutingDecision, decide_route


@dataclass(frozen=True)
class SupportDecision:
    classification: Classification
    routing: RoutingDecision


class SupportDecisionEngine:
    def __init__(self, classifier=None):
        self.classifier = classifier or LLMClassifier()

    def decide(
        self,
        ticket_text: str,
        must_not_auto_respond: bool = False,
    ) -> SupportDecision:
        classification = self.classifier.classify(ticket_text)

        routing = decide_route(
            classification,
            must_not_auto_respond=must_not_auto_respond,
        )

        return SupportDecision(
            classification=classification,
            routing=routing,
        )
