from cloudserve_support.classification import (
    Classification,
    INTENTS,
    URGENCIES,
)


def test_classification_model():
    result = Classification(
        intent="authentication_failure",
        urgency="high",
        confidence=0.95,
    )

    assert result.intent in INTENTS
    assert result.urgency in URGENCIES
    assert 0.0 <= result.confidence <= 1.0
