import json

from .response import SupportResponse


def parse_response(content: str) -> SupportResponse:
    data = json.loads(content)

    response = data["response"]
    source_references = tuple(data.get("source_references", []))
    machine_generated_disclosure = bool(
        data.get("machine_generated_disclosure", False)
    )
    grounded = bool(data.get("grounded", False))

    if not isinstance(response, str) or not response.strip():
        raise ValueError("Response must be a non-empty string.")

    if not all(isinstance(ref, str) for ref in source_references):
        raise ValueError("Source references must be strings.")

    return SupportResponse(
        response=response,
        source_references=source_references,
        machine_generated_disclosure=machine_generated_disclosure,
        grounded=grounded,
    )
