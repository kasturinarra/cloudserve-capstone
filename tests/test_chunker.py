from cloudserve_support.chunker import chunk_document, chunk_documents
from cloudserve_support.document_loader import load_documents


def test_chunk_single_document():
    documents = load_documents("data/documentation.json")

    chunks = chunk_document(documents[0], max_chars=500, overlap=50)

    assert chunks
    assert all(chunk.doc_id == "DOC-AUTH-001" for chunk in chunks)
    assert chunks[0].chunk_id == "DOC-AUTH-001-chunk-000"
    assert all(chunk.content for chunk in chunks)


def test_chunk_all_documents():
    documents = load_documents("data/documentation.json")

    chunks = chunk_documents(documents)

    assert chunks
    assert len({chunk.doc_id for chunk in chunks}) == 29
