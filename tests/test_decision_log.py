import sqlite3

from cloudserve_support.classification import Classification
from cloudserve_support.decision_log import DecisionLogger
from cloudserve_support.routing import RoutingDecision


def test_decision_is_persisted(tmp_path):
    database_path = tmp_path / "decisions.db"

    logger = DecisionLogger(database_path)

    classification = Classification(
        intent="configuration_help",
        urgency="low",
        confidence=0.95,
    )

    routing = RoutingDecision(
        route="auto_respond",
        reason="classification passed routing checks",
    )

    logger.log(
        ticket_id="TEST-001",
        classification=classification,
        routing=routing,
        retrieved_doc_ids=["DOC-CONFIG-001", "DOC-CONFIG-002"],
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT ticket_id, intent, urgency, confidence,
                   route, routing_reason, retrieved_doc_ids
            FROM decisions
            WHERE ticket_id = ?
            """,
            ("TEST-001",),
        ).fetchone()

    assert row == (
        "TEST-001",
        "configuration_help",
        "low",
        0.95,
        "auto_respond",
        "classification passed routing checks",
        "DOC-CONFIG-001,DOC-CONFIG-002",
    )
