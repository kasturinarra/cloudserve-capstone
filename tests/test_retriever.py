from cloudserve_support.document_loader import load_documents
from cloudserve_support.retriever import Retriever


def test_retrieval_finds_authentication_document():
    documents = load_documents("data/documentation.json")
    retriever = Retriever(documents)

    results = retriever.search(
        "My login says invalid credentials. How can I fix it?",
        top_k=3,
    )

    assert len(results) == 3
    assert results[0][0].doc_id == "DOC-AUTH-001"


def test_retrieval_returns_scores():
    documents = load_documents("data/documentation.json")
    retriever = Retriever(documents)

    results = retriever.search(
        "How do I fix invalid credentials?",
        top_k=3,
    )

    assert all(isinstance(score, float) for _, score in results)
    assert results[0][1] >= results[1][1]
