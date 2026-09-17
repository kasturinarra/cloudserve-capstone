import re

from .response import SupportResponse


EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"
)

API_KEY_PATTERN = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{10,}|"
    r"api[_-]?key[=:]\s*[A-Za-z0-9_-]{8,}|"
    r"token[=:]\s*[A-Za-z0-9_-]{8,})\b",
    re.IGNORECASE,
)


def validate_response(
    response: SupportResponse,
    retrieved_documents=None,
) -> None:
    """Raise ValueError if a generated response is not safe to send."""

    if not response.grounded:
        raise ValueError("Response is not grounded in controlled documentation.")

    if not response.machine_generated_disclosure:
        raise ValueError("Response is missing machine-generated disclosure.")

    if not response.source_references:
        raise ValueError("Response does not contain a source reference.")

    if retrieved_documents is not None:
        retrieved_doc_ids = {
            chunk.doc_id
            for chunk, _score in retrieved_documents
        }

        invalid_references = [
            ref
            for ref in response.source_references
            if ref not in retrieved_doc_ids
        ]

        if invalid_references:
            raise ValueError(
                "Response contains source references that were not retrieved: "
                + ", ".join(invalid_references)
            )

    response_text = response.response

    if EMAIL_PATTERN.search(response_text):
        raise ValueError("Response contains potentially private email data.")

    if PHONE_PATTERN.search(response_text):
        raise ValueError("Response contains potentially private phone data.")

    if API_KEY_PATTERN.search(response_text):
        raise ValueError("Response contains potentially private credential data.")
