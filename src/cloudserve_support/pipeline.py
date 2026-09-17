from dataclasses import dataclass

from .classification import Classification
from .data_loader import load_tickets
from .document_loader import load_documents
from .llm_classifier import LLMClassifier
from .llm_client import LLMProviderError
from .response import SupportResponse
from .response_generator import ResponseGenerator
from .retriever import Retriever
from .routing import RoutingDecision, decide_route
from .guardrails import validate_response
from .decision_log import DecisionLogger


@dataclass(frozen=True)
class PipelineResult:
    ticket_id: str
    classification: Classification
    routing: RoutingDecision
    retrieved_documents: list
    response: SupportResponse | None


class SupportPipeline:
    def __init__(
        self,
        documents,
        classifier=None,
        response_generator=None,
        retriever=None,
        decision_logger=None,
    ):
        self.classifier = classifier or LLMClassifier()
        self.retriever = retriever or Retriever(documents)
        self.response_generator = response_generator or ResponseGenerator()
        self.decision_logger = decision_logger or DecisionLogger()

    def process(self, ticket):
        classification = self.classifier.classify(ticket.text)

        routing = decide_route(
            classification,
            must_not_auto_respond=ticket.must_not_auto_respond,
        )

        retrieved_documents = self.retriever.search(
            ticket.text,
            top_k=5,
        )

        if routing.route == "auto_respond" and not retrieved_documents:
            routing = RoutingDecision(
                route="escalate",
                reason="no relevant controlled documentation was retrieved",
            )

        response = None

        if routing.route == "auto_respond":
            try:
                response = self.response_generator.generate(
                    ticket_text=ticket.text,
                    retrieved_documents=retrieved_documents,
                    intent=classification.intent,
                    urgency=classification.urgency,
                    route=routing.route,
                )

                validate_response(response)
                validate_response(
                    response,
                    retrieved_documents=retrieved_documents,
                )

            except LLMProviderError:
                routing = RoutingDecision(
                    route="escalate",
                    reason=(
                        "response generation unavailable because "
                        "the model provider failed"
                    ),
                )
                response = None

            except ValueError as exc:
                routing = RoutingDecision(
                    route="escalate",
                    reason=f"generated response blocked by guardrail: {exc}",
                )
                response = None

        self.decision_logger.log(
            ticket_id=ticket.ticket_id,
            classification=classification,
            routing=routing,
            retrieved_doc_ids=[
                chunk.doc_id for chunk, _score in retrieved_documents
            ],
        )

        return PipelineResult(
            ticket_id=ticket.ticket_id,
            classification=classification,
            routing=routing,
            retrieved_documents=retrieved_documents,
            response=response,
        )

