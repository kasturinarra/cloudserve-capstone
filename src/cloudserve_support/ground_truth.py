import json
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class GroundTruth:
    ticket_id: str
    intent: str
    expected_doc_ids: tuple[str, ...]
    reference_response: str
    must_mention: tuple[str, ...]
    must_not_claim: tuple[str, ...]


def load_ground_truth(path: str | Path) -> list[GroundTruth]:
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected ground-truth data to contain a JSON list.")

    return [
        GroundTruth(
            ticket_id=record["ticket_id"],
            intent=record["intent"],
            expected_doc_ids=tuple(record.get("expected_doc_ids", [])),
            reference_response=record["reference_response"],
            must_mention=tuple(record.get("must_mention", [])),
            must_not_claim=tuple(record.get("must_not_claim", [])),
        )
        for record in records
    ]
