from cloudserve_support.classification import Classification
from cloudserve_support.routing import decide_route


def test_sensitive_intent_escalates():
    classification = Classification(
        intent="security_incident",
        urgency="high",
        confidence=0.95,
    )

    result = decide_route(classification)

    assert result.route == "escalate"


def test_low_confidence_escalates():
    classification = Classification(
        intent="configuration_help",
        urgency="medium",
        confidence=0.70,
    )

    result = decide_route(classification)

    assert result.route == "escalate"


def test_must_not_auto_respond_escalates():
    classification = Classification(
        intent="configuration_help",
        urgency="low",
        confidence=0.95,
    )

    result = decide_route(
        classification,
        must_not_auto_respond=True,
    )

    assert result.route == "escalate"


def test_safe_high_confidence_ticket_auto_responds():
    classification = Classification(
        intent="configuration_help",
        urgency="low",
        confidence=0.95,
    )

    result = decide_route(classification)

    assert result.route == "auto_respond"
