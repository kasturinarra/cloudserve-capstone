from .data_loader import load_tickets
from .ground_truth import load_ground_truth
from .retriever import Retriever


def retrieval_recall_at_k(
    tickets,
    ground_truth,
    retriever,
    k: int = 5,
) -> float:
    ticket_by_id = {ticket.ticket_id: ticket for ticket in tickets}

    hits = 0
    evaluated = 0

    for truth in ground_truth:
        ticket = ticket_by_id[truth.ticket_id]

        results = retriever.search(ticket.text, top_k=k)
        retrieved_doc_ids = {chunk.doc_id for chunk, _ in results}

        if retrieved_doc_ids.intersection(truth.expected_doc_ids):
            hits += 1

        evaluated += 1

    return hits / evaluated if evaluated else 0.0
