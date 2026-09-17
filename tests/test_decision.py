from cloudserve_support.classification import Classification
from cloudserve_support.decision import SupportDecisionEngine


class FakeClassifier:
    def classify(self, ticket_text):
        return Classification(
            intent="configuration_help",
            urgency="low",
            confidence=0.95,
        )


def test_decision_engine_combines_classification_and_routing():
    engine = SupportDecisionEngine(classifier=FakeClassifier())

    result = engine.decide("How do I configure this?")

    assert result.classification.intent == "configuration_help"
    assert result.classification.urgency == "low"
    assert result.classification.confidence == 0.95
    assert result.routing.route == "auto_respond"


def test_decision_engine_honors_must_not_auto_respond():
    engine = SupportDecisionEngine(classifier=FakeClassifier())

    result = engine.decide(
        "How do I configure this?",
        must_not_auto_respond=True,
    )

    assert result.routing.route == "escalate"
