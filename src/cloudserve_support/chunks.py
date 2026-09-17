from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    doc_id: str
    title: str
    category: str
    content: str
    chunk_index: int
