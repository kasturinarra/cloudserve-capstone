from cloudserve_support.data_loader import load_tickets


def test_load_validation_tickets():
    tickets = load_tickets("data/validation_tickets.json")

    assert len(tickets) == 80
    assert tickets[0].ticket_id == "VAL-0001"
    assert tickets[0].text
