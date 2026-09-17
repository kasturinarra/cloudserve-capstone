from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedTicket:
    ticket_id: str
    channel: str
    subject: str
    body: str
    received_at: str
    customer_id: str
    customer_tier: str
    customer_region: str
    language_fluency: str
    must_not_auto_respond: bool = False

    @property
    def text(self) -> str:
        """Return the customer-facing text used by downstream processing."""
        subject = self.subject.strip()
        body = self.body.strip()

        if subject and body:
            return f"{subject}\n\n{body}"

        return subject or body
