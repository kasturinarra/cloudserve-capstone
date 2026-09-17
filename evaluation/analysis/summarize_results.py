import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: python summarize_results.py <evaluation_results.json>")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data["summary"]

    print("=== Evaluation Analysis ===")
    print(f"Total: {summary['total']}")
    print(f"Completed: {summary['completed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Completion rate: {summary['completion_rate'] * 100:.1f}%")

    for key, label in (
        ("intent_accuracy", "Intent accuracy"),
        ("retrieval_recall_at_5", "Retrieval Recall@5"),
        ("source_reference_validity", "Source-reference validity"),
        ("required_mention_compliance", "Required-mention compliance"),
        ("must_not_claim_compliance", "Must-not-claim compliance"),
    ):
        if key in summary:
            print(f"{label}: {summary[key] * 100:.1f}%")

    for key, label in (
        ("mean_latency_ms", "Mean latency"),
        ("median_latency_ms", "Median latency"),
        ("p95_latency_ms", "P95 latency"),
    ):
        if key in summary:
            print(f"{label}: {summary[key]:.2f} ms")

    print(f"Failure counts: {summary.get('failure_counts', {})}")


if __name__ == "__main__":
    main()
