import argparse
import json
import time
import statistics
from collections import Counter
from pathlib import Path

from .data_loader import load_tickets
from .document_loader import load_documents
from .ground_truth import load_ground_truth
from .pipeline import SupportPipeline

def source_references_valid(result):
    if result.response is None:
        return False

    retrieved_doc_ids = {
        chunk.doc_id
        for chunk, _score in result.retrieved_documents
    }

    return all(
        reference in retrieved_doc_ids
        for reference in result.response.source_references
    )


def required_mentions_present(result, ground_truth):
    if result.response is None:
        return False

    response_text = result.response.response.lower()

    return all(
        phrase.lower() in response_text
        for phrase in ground_truth.must_mention
    )


def must_not_claims_absent(result, ground_truth):
    if result.response is None:
        return False

    response_text = result.response.response.lower()

    return all(
        phrase.lower() not in response_text
        for phrase in ground_truth.must_not_claim
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run CloudServe support pipeline evaluation."
    )
    parser.add_argument("--tickets", required=True)
    parser.add_argument("--documents", required=True)
    parser.add_argument("--ground-truth")
    parser.add_argument(
        "--output",
        default="storage/evaluation_results.json",
    )

    args = parser.parse_args()

    tickets = load_tickets(args.tickets)
    documents = load_documents(args.documents)

    ground_truth_by_id = {}

    if args.ground_truth:
        ground_truth = load_ground_truth(args.ground_truth)
        ground_truth_by_id = {
            item.ticket_id: item
            for item in ground_truth
        }

    pipeline = SupportPipeline(documents)

    results = []

    for ticket in tickets:
        try:
            start_time = time.perf_counter()
            result = pipeline.process(ticket)

            processing_time_ms = (
                time.perf_counter() - start_time
            ) * 1000

            results.append(
                {
                    "ticket_id": result.ticket_id,
                    "status": "completed",
                    "intent": result.classification.intent,
                    "urgency": result.classification.urgency,
                    "confidence": result.classification.confidence,


                    "processing_time_ms": processing_time_ms,
                    "processing_time_ms": processing_time_ms,
                    "route": result.routing.route,
                    "routing_reason": result.routing.reason,
                    "retrieved_doc_ids": [
                        chunk.doc_id
                        for chunk, _score in result.retrieved_documents
                    ],
                    "response_generated": result.response is not None,
                    "response_grounded": (
                        result.response.grounded
                        if result.response
                        else None
                    ),
                    "source_references": (
                        list(result.response.source_references)
                        if result.response
                        else []
                    ),
                    "source_references_valid": (
                        source_references_valid(result)
                        if result.response
                        else False
                    ),
                    "required_mentions_present": (
                        required_mentions_present(
                        result,
                        ground_truth_by_id[result.ticket_id],
                    )
                    if result.response
                    and result.ticket_id in ground_truth_by_id
                    else None
                    ),
                    "must_not_claims_absent": (
                        must_not_claims_absent(
                            result,
                            ground_truth_by_id[result.ticket_id],
                    )
                    if result.response
                    and result.ticket_id in ground_truth_by_id
                    else None
                    ),
                }
            )

            print(
                f"{ticket.ticket_id}: "
                f"{result.classification.intent} / "
                f"{result.classification.urgency} / "
                f"{result.routing.route}"
            )

        except Exception as exc:
            error_type = "pipeline_failure"
            error_message = str(exc)

            if type(exc).__name__ == "JSONDecodeError":
                error_type = "llm_output_failure"
            elif "Invalid intent" in error_message:
                error_type = "classification_failure"
            elif "Invalid urgency" in error_message:
                error_type = "classification_failure"
            elif "confidence" in error_message.lower():
                error_type = "classification_failure"
            elif (
                "Response is not grounded" in error_message
                or "Response does not contain a source reference" in error_message
                or "Response is missing machine-generated disclosure"
                in error_message
            ):
                error_type = "guardrail_failure"

            results.append(
                {
                    "ticket_id": ticket.ticket_id,
                    "status": "failed",
                    "failure_type": error_type,
                    "error": error_message,
                }
            )

            print(
                f"{ticket.ticket_id}: FAILED - "
                f"{error_type} - {type(exc).__name__}: {exc}"
            )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        "total": len(results),
        "completed": sum(
            1 for result in results
            if result["status"] == "completed"
        ),
        "failed": sum(
            1 for result in results
            if result["status"] == "failed"
        ),
    }

    summary["completion_rate"] = (
        summary["completed"] / summary["total"]
        if summary["total"]
        else 0.0
    )

    latencies = [
        result["processing_time_ms"]
        for result in results
        if result["status"] == "completed"
    ]

    if latencies:
        sorted_latencies = sorted(latencies)
        p95_index = max(0, int(0.95 * len(sorted_latencies)) - 1)

        summary["mean_latency_ms"] = statistics.mean(latencies)
        summary["median_latency_ms"] = statistics.median(latencies)
        summary["p95_latency_ms"] = sorted_latencies[p95_index]

    failure_counts = Counter(
        result["failure_type"]
        for result in results
        if result["status"] == "failed"
    )

    summary["failure_counts"] = dict(failure_counts)

    if ground_truth_by_id:
        completed = [
            result
            for result in results
            if result["status"] == "completed"
            and result["ticket_id"] in ground_truth_by_id
        ]

        response_evaluated = [
            result
            for result in completed
            if result["route"] == "auto_respond"
            and result["response_generated"]
        ]

        intent_correct = sum(
            result["intent"]
            == ground_truth_by_id[result["ticket_id"]].intent
            for result in completed
        )

        retrieval_hits = sum(
            bool(
                set(
                    result["retrieved_doc_ids"]
                )
                & set(
                    ground_truth_by_id[
                        result["ticket_id"]
                    ].expected_doc_ids
                )
            )
            for result in completed
        )

        evaluated = len(completed)

        summary["intent_accuracy"] = (
            intent_correct / evaluated
            if evaluated
            else 0.0
        )

        summary["retrieval_recall_at_5"] = (
            retrieval_hits / evaluated
            if evaluated
            else 0.0
        )

        response_evaluated_count = len(response_evaluated)

        source_valid = sum(
            result["source_references_valid"]
            for result in response_evaluated
        )

        mentions_correct = sum(
            result["required_mentions_present"]
            for result in response_evaluated
        )

        claims_safe = sum(
            result["must_not_claims_absent"]
            for result in response_evaluated
        )

        summary["source_reference_validity"] = (
            source_valid / response_evaluated_count
            if response_evaluated_count
            else 0.0
        )

        summary["required_mention_compliance"] = (
            mentions_correct / response_evaluated_count
            if response_evaluated_count
            else 0.0
        )

        summary["must_not_claim_compliance"] = (
            claims_safe / response_evaluated_count
            if response_evaluated_count
            else 0.0
        )

    output = {
        "summary": summary,
        "results": results,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print()
    print("=== Evaluation Summary ===")
    print(f"Total: {summary['total']}")
    print(f"Completed: {summary['completed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Completion rate: {summary['completion_rate'] * 100:.1f}%")

    if "mean_latency_ms" in summary:
        print(f"Mean latency: {summary['mean_latency_ms']:.2f} ms")
        print(f"Median latency: {summary['median_latency_ms']:.2f} ms")
        print(f"P95 latency: {summary['p95_latency_ms']:.2f} ms")

    if "intent_accuracy" in summary:
        print(
            f"Intent accuracy: "
            f"{summary['intent_accuracy'] * 100:.1f}%"
        )
        print(
            f"Retrieval Recall@5: "
            f"{summary['retrieval_recall_at_5'] * 100:.1f}%"
        )
        print(
            f"Source-reference validity: "
            f"{summary['source_reference_validity'] * 100:.1f}%"
        )
        print(
            f"Required-mention compliance: "
            f"{summary['required_mention_compliance'] * 100:.1f}%"
        )
        print(
            f"Must-not-claim compliance: "
             f"{summary['must_not_claim_compliance'] * 100:.1f}%"
        )

    print(f"Failure counts: {summary['failure_counts']}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
