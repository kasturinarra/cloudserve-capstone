import sqlite3
from pathlib import Path

from .classification import Classification
from .routing import RoutingDecision


class DecisionLogger:
    def __init__(self, database_path: str | Path = "storage/decisions.db"):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _create_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    ticket_id TEXT PRIMARY KEY,
                    intent TEXT NOT NULL,
                    urgency TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    route TEXT NOT NULL,
                    routing_reason TEXT NOT NULL,
                    retrieved_doc_ids TEXT NOT NULL
                )
                """
            )

    def log(
        self,
        ticket_id: str,
        classification: Classification,
        routing: RoutingDecision,
        retrieved_doc_ids: list[str],
    ):
        doc_ids = ",".join(retrieved_doc_ids)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO decisions (
                    ticket_id,
                    intent,
                    urgency,
                    confidence,
                    route,
                    routing_reason,
                    retrieved_doc_ids
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    classification.intent,
                    classification.urgency,
                    classification.confidence,
                    routing.route,
                    routing.reason,
                    doc_ids,
                ),
            )
