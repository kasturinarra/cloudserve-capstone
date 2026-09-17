import json
from pathlib import Path

from .models import NormalizedTicket


def load_tickets(path: str | Path) -> list[NormalizedTicket]:
    """Load raw ticket JSON and convert it to normalized tickets."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Expected the ticket dataset to contain a JSON list.")

    tickets = []

    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each ticket record must be a JSON object.")

        tickets.append(
            NormalizedTicket(
                ticket_id=record["ticket_id"],
                channel=record["channel"],
                subject=record.get("subject", ""),
                body=record["body"],
                received_at=record["received_at"],
                customer_id=record["customer_id"],
                customer_tier=record["customer_tier"],
                customer_region=record["customer_region"],
                language_fluency=record["language_fluency"],
                must_not_auto_respond=record.get("labels", {}).get(
                    "must_not_auto_respond", False
                ),
            )
        )

    return tickets
