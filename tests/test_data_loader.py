from cloudserve_support.data_loader import load_tickets
from cloudserve_support.models import NormalizedTicket


def test_load_sample_tickets():
    tickets = load_tickets("data/sample_tickets.json")

    assert len(tickets) == 3
    assert isinstance(tickets[0], NormalizedTicket)


def test_normalized_ticket_text():
    tickets = load_tickets("data/sample_tickets.json")

    ticket = tickets[0]

    assert ticket.ticket_id == "DEV-0001"
    assert ticket.channel == "chat"
    assert ticket.text
