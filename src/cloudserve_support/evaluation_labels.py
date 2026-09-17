import json
from pathlib import Path


def load_evaluation_labels(path: str | Path) -> dict[str, dict]:
    """Load ground-truth labels for evaluation only."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected the dataset to contain a JSON list.")

    labels = {}

    for record in records:
        ticket_id = record["ticket_id"]
        ticket_labels = record["labels"]

        labels[ticket_id] = {
            "intent": ticket_labels["intent"],
            "urgency": ticket_labels["urgency"],
            "expected_route": ticket_labels["expected_route"],
        }

    return labels
