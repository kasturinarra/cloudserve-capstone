import re

from .chunks import DocumentChunk
from .document_models import Document


SECTION_PATTERN = re.compile(r"(?=^##\s+)", re.MULTILINE)


def chunk_document(
    document: Document,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[DocumentChunk]:
    """Split a controlled document primarily at Markdown section boundaries."""

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap must not be negative.")

    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars.")

    text = document.content.strip()

    if not text:
        return []

    sections = [section.strip() for section in SECTION_PATTERN.split(text) if section.strip()]

    chunks: list[DocumentChunk] = []

    for section in sections:
        if len(section) <= max_chars:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document.doc_id}-chunk-{len(chunks):03d}",
                    doc_id=document.doc_id,
                    title=document.title,
                    category=document.category,
                    content=section,
                    chunk_index=len(chunks),
                )
            )
            continue

        # Very large sections are split into overlapping character windows.
        start = 0

        while start < len(section):
            end = min(start + max_chars, len(section))
            chunk_text = section[start:end].strip()

            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.doc_id}-chunk-{len(chunks):03d}",
                        doc_id=document.doc_id,
                        title=document.title,
                        category=document.category,
                        content=chunk_text,
                        chunk_index=len(chunks),
                    )
                )

            if end >= len(section):
                break

            start = end - overlap

    return chunks


def chunk_documents(
    documents: list[Document],
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[DocumentChunk]:
    """Chunk all controlled documents."""
    chunks: list[DocumentChunk] = []

    for document in documents:
        chunks.extend(
            chunk_document(
                document,
                max_chars=max_chars,
                overlap=overlap,
            )
        )

    return chunks
