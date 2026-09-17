import pytest

from cloudserve_support.classifier import parse_classification


def test_parse_valid_classification():
    result = parse_classification(
        '{"intent": "authentication_failure", '
        '"urgency": "high", "confidence": 0.95}'
    )

    assert result.intent == "authentication_failure"
    assert result.urgency == "high"
    assert result.confidence == 0.95


def test_reject_invalid_intent():
    with pytest.raises(ValueError):
        parse_classification(
            '{"intent": "made_up_intent", '
            '"urgency": "high", "confidence": 0.95}'
        )


def test_reject_invalid_confidence():
    with pytest.raises(ValueError):
        parse_classification(
            '{"intent": "authentication_failure", '
            '"urgency": "high", "confidence": 1.5}'
        )
