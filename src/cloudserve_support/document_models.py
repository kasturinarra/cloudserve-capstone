from dataclasses import dataclass


@dataclass(frozen=True)
class Document:
    doc_id: str
    title: str
    category: str
    applies_to: str
    content: str
    related_docs: tuple[str, ...]
    last_reviewed_days_ago: int
