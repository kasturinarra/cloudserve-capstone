from cloudserve_support.data_loader import load_tickets


def test_load_validation_tickets():
    tickets = load_tickets("data/sample_tickets.json")

    assert len(tickets) == 3
    assert tickets[0].ticket_id == "DEV-0001"
    assert tickets[0].text
