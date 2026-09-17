import pytest

from cloudserve_support.guardrails import validate_response
from cloudserve_support.response import SupportResponse


def test_guardrail_accepts_safe_response():
    response = SupportResponse(
        response="Follow the documented steps.",
        source_references=("DOC-001",),
        machine_generated_disclosure=True,
        grounded=True,
    )

    validate_response(response)


def test_guardrail_rejects_ungrounded_response():
    response = SupportResponse(
        response="This should not be sent.",
        source_references=("DOC-001",),
        machine_generated_disclosure=True,
        grounded=False,
    )

    with pytest.raises(ValueError, match="not grounded"):
        validate_response(response)


def test_guardrail_rejects_missing_disclosure():
    response = SupportResponse(
        response="This should not be sent.",
        source_references=("DOC-001",),
        machine_generated_disclosure=False,
        grounded=True,
    )

    with pytest.raises(ValueError, match="disclosure"):
        validate_response(response)


def test_guardrail_rejects_missing_source():
    response = SupportResponse(
        response="This should not be sent.",
        source_references=(),
        machine_generated_disclosure=True,
        grounded=True,
    )

    with pytest.raises(ValueError, match="source reference"):
        validate_response(response)
