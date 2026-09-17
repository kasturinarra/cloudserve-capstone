from cloudserve_support.classification import Classification
from cloudserve_support.pipeline import SupportPipeline
from cloudserve_support.response import SupportResponse
from cloudserve_support.routing import RoutingDecision


class FakeClassifier:
    def classify(self, ticket_text):
        return Classification(
            intent="configuration_help",
            urgency="low",
            confidence=0.95,
        )


class FakeChunk:
    doc_id = "DOC-CONFIG-001"

class FakeRetriever:
    def search(self, query, top_k=5):
        return [(FakeChunk(), 0.90)]


class FakeResponseGenerator:
    def generate(
        self,
        ticket_text,
        retrieved_documents,
        intent,
        urgency,
        route,
    ):
        return SupportResponse(
            response="Please follow the configuration documentation.",
            source_references=("DOC-CONFIG-001",),
            machine_generated_disclosure=True,
            grounded=True,
        )


class FakeTicket:
    ticket_id = "TEST-001"
    text = "How do I configure this?"
    must_not_auto_respond = False


def test_pipeline_processes_safe_ticket():
    pipeline = SupportPipeline(
        documents=[],
        classifier=FakeClassifier(),
        retriever=FakeRetriever(),
        response_generator=FakeResponseGenerator(),
    )

    result = pipeline.process(FakeTicket())

    assert result.ticket_id == "TEST-001"
    assert result.classification.intent == "configuration_help"
    assert result.routing.route == "auto_respond"
    assert result.response is not None
    assert result.response.grounded is True

def test_pipeline_escalates_must_not_auto_respond_ticket():
    pipeline = SupportPipeline(
        documents=[],
        classifier=FakeClassifier(),
        retriever=FakeRetriever(),
        response_generator=FakeResponseGenerator(),
    )

    ticket = FakeTicket()
    ticket.must_not_auto_respond = True

    result = pipeline.process(ticket)

    assert result.routing.route == "escalate"
    assert result.response is None

def test_pipeline_logs_decision_before_guardrail_failure(tmp_path):
    class FailingResponseGenerator:
        def generate(
            self,
            ticket_text,
            retrieved_documents,
            intent,
            urgency,
            route,
        ):
            return SupportResponse(
                response="Unsafe response",
                source_references=("DOC-001",),
                machine_generated_disclosure=True,
                grounded=False,
            )

    from cloudserve_support.decision_log import DecisionLogger

    database_path = tmp_path / "decisions.db"

    pipeline = SupportPipeline(
        documents=[],
        classifier=FakeClassifier(),
        retriever=FakeRetriever(),
        response_generator=FailingResponseGenerator(),
        decision_logger=DecisionLogger(database_path),
    )

    ticket = FakeTicket()

    import pytest

    result = pipeline.process(ticket)
    assert result.routing.route == "escalate"
    assert "guardrail" in result.routing.reason

    import sqlite3

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT ticket_id, intent, urgency, route
            FROM decisions
            WHERE ticket_id = ?
            """,
            (ticket.ticket_id,),
        ).fetchone()

    assert row is not None
    assert row[0] == ticket.ticket_id
    assert row[3] == "escalate"

def test_pipeline_escalates_when_no_documentation_is_retrieved():
    pipeline = SupportPipeline(
        documents=[],
        classifier=FakeClassifier(),
        retriever=FakeRetrieverWithNoResults(),
        response_generator=FakeResponseGenerator(),
    )

    result = pipeline.process(FakeTicket())

    assert result.routing.route == "escalate"
    assert result.routing.reason == (
        "no relevant controlled documentation was retrieved"
    )
    assert result.response is None

class FakeRetrieverWithNoResults:
    def search(self, query, top_k=5):
        return []

