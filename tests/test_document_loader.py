from cloudserve_support.document_loader import load_documents
from cloudserve_support.document_models import Document


def test_load_documents():
    documents = load_documents("data/documentation.json")

    assert len(documents) == 29
    assert isinstance(documents[0], Document)


def test_first_document():
    documents = load_documents("data/documentation.json")

    document = documents[0]

    assert document.doc_id == "DOC-AUTH-001"
    assert document.title == "Resolving invalid credential errors on login"
    assert document.category == "authentication"
    assert document.content
