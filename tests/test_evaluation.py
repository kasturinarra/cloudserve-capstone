from cloudserve_support.data_loader import load_tickets
from cloudserve_support.document_loader import load_documents
from cloudserve_support.ground_truth import load_ground_truth
from cloudserve_support.evaluation import retrieval_recall_at_k
from cloudserve_support.retriever import Retriever


def test_retrieval_recall_at_5():
    tickets = load_tickets("tests/fixtures/retrieval_tickets.json")
    documents = load_documents("data/documentation.json")
    ground_truth = load_ground_truth("tests/fixtures/retrieval_ground_truth.json")

    retriever = Retriever(documents)

    score = retrieval_recall_at_k(
        tickets,
        ground_truth,
        retriever,
        k=5,
    )

    assert score >= 0.90
