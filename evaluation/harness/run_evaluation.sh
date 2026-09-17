#!/usr/bin/env bash
set -euo pipefail

TICKETS="${1:?Usage: $0 <tickets.json> <documents.json> [ground_truth.json] [output.json]}"
DOCUMENTS="${2:?Usage: $0 <tickets.json> <documents.json> [ground_truth.json] [output.json]}"
GROUND_TRUTH="${3:-}"
OUTPUT="${4:-evaluation/results/evaluation_results.json}"

mkdir -p "$(dirname "$OUTPUT")"

if [[ -n "$GROUND_TRUTH" ]]; then
    python -m cloudserve_support.evaluate \
        --tickets "$TICKETS" \
        --documents "$DOCUMENTS" \
        --ground-truth "$GROUND_TRUTH" \
        --output "$OUTPUT"
else
    python -m cloudserve_support.evaluate \
        --tickets "$TICKETS" \
        --documents "$DOCUMENTS" \
        --output "$OUTPUT"
fi
