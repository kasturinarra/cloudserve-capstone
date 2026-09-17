from dataclasses import dataclass

from .classification import Classification


SENSITIVE_INTENTS = {
    "security_incident",
    "compliance_request",
    "data_residency",
    "billing_query",
    "data_export",
}


@dataclass(frozen=True)
class RoutingDecision:
    route: str
    reason: str


def decide_route(
    classification: Classification,
    must_not_auto_respond: bool = False,
    confidence_threshold: float = 0.80,
) -> RoutingDecision:
    if must_not_auto_respond:
        return RoutingDecision(
            route="escalate",
            reason="ticket is marked must_not_auto_respond",
        )

    if classification.intent in SENSITIVE_INTENTS:
        return RoutingDecision(
            route="escalate",
            reason=f"sensitive intent: {classification.intent}",
        )

    if classification.confidence < confidence_threshold:
        return RoutingDecision(
            route="escalate",
            reason="classification confidence below threshold",
        )

    return RoutingDecision(
        route="auto_respond",
        reason="classification passed routing checks",
    )
