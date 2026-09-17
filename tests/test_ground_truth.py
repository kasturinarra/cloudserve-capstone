from cloudserve_support.ground_truth import GroundTruth, load_ground_truth


def test_load_ground_truth():
    records = load_ground_truth("tests/fixtures/retrieval_ground_truth.json")

    assert len(records) == 1
    assert isinstance(records[0], GroundTruth)
    assert records[0].ticket_id == "DEV-0485"
    assert records[0].expected_doc_ids == ("DOC-ACCT-001",)
