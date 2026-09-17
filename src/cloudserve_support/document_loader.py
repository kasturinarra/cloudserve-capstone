import json
from pathlib import Path

from .document_models import Document


def load_documents(path: str | Path) -> list[Document]:
    """Load the controlled documentation dataset."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected the documentation dataset to contain a JSON list.")

    documents = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each document record must be a JSON object.")

        documents.append(
            Document(
                doc_id=record["doc_id"],
                title=record["title"],
                category=record["category"],
                applies_to=record["applies_to"],
                content=record["content"],
                related_docs=tuple(record.get("related_docs", [])),
                last_reviewed_days_ago=record["last_reviewed_days_ago"],
            )
        )

    return documents
