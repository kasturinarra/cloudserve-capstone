# CloudServe Solutions — Intelligent Customer Support

An intelligent customer support system that normalizes incoming tickets, classifies intent and urgency, retrieves relevant controlled documentation, generates grounded responses, applies safety guardrails, routes uncertain or sensitive tickets to human support, and records processing decisions.

## 1. System Overview

CloudServe processes support requests through a controlled pipeline:

```text
Ticket Input
    |
    v
Normalization
    |
    v
Intent + Urgency Classification
    |
    v
Deterministic Routing
    |
    +----------------------+
    |                      |
    | Escalate             | Auto-response eligible
    v                      v
Human Support       Controlled Documentation Retrieval
                           |
                           +----------------------+
                           |                      |
                     No relevant docs       Relevant docs
                           |                      |
                           v                      v
                     Human Support        Response Generation
                                                  |
                                                  v
                                          Guardrail Validation
                                                  |
                                    +-------------+-------------+
                                    |                           |
                                  Block                        Pass
                                    |                           |
                                    v                           v
                              Human Support             Customer Response

All processing paths
        |
        v
Persistent Decision Log
```

The system is designed so that:

* customer-provided text is treated as untrusted input;
* controlled documentation is the evidence source for automated answers;
* routing is deterministic and independent of generated response content;
* sensitive, uncertain, unsupported, or blocked cases are escalated;
* every processed ticket produces a persistent decision record;
* evaluation can be run unattended against a supplied input file.

## 2. Requirements

* Python 3.14+
* `uv`
* An OpenRouter API key
* Internet access for the configured model provider

The implementation uses:

* OpenRouter for LLM inference
* `meta-llama/llama-3.1-8b-instruct` as the configured LLM
* Sentence Transformers for document embeddings
* `all-MiniLM-L6-v2` as the configured embedding model
* SQLite for persistent decision logging
* pytest for automated tests

The system is designed to use free-tier-compatible services and does not require a paid model provider.

## 3. Repository Structure

```text
cloudserve-capstone/
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── README.md
├── data/
│   ├── documentation.json
│   └── sample_tickets.json
├── docs/
│   └── architecture/
│       └── architecture.md
├── evaluation/
│   ├── analysis/
│   │   └── summarize_results.py
│   ├── harness/
│   │   └── run_evaluation.sh
│   └── results/
├── prompts/
│   ├── PR-01_classifier_v1.txt
│   ├── PR-02_grounded_response_v1.txt
│   └── PR-03_evaluator_v1.txt
├── pyproject.toml
├── requirements.txt
├── src/
│   └── cloudserve_support/
│       ├── classifier.py
│       ├── data_loader.py
│       ├── decision_log.py
│       ├── document_loader.py
│       ├── embedder.py
│       ├── evaluate.py
│       ├── evaluation.py
│       ├── ground_truth.py
│       ├── guardrails.py
│       ├── llm_classifier.py
│       ├── llm_client.py
│       ├── models.py
│       ├── pipeline.py
│       ├── response_generator.py
│       ├── response_parser.py
│       ├── retriever.py
│       └── routing.py
└── tests/
```

The full supplied evaluation datasets and generated evaluation results are intentionally excluded from the source repository. The repository contains a small sanitized sample for reproducibility and demonstration.

## 4. Installation

Clone the repository:

```bash
git clone https://github.com/kasturinarra/cloudserve-capstone.git
cd cloudserve-capstone
```

Create the virtual environment:

```bash
uv venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
uv pip install -r requirements.txt
```

Install the project itself in editable mode:

```bash
uv pip install -e .
```

## 5. Configuration

Create the environment file:

```bash
cp .env.example .env
```

Set the OpenRouter API key in `.env`:

```text
OPENROUTER_API_KEY=<your-key>
```

The default configuration is:

```text
MODEL_NAME=meta-llama/llama-3.1-8b-instruct
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PATH=storage/chroma
DATABASE_URL=storage/decisions.db
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD=0.80
RETRIEVAL_TOP_K=5
```

Do not commit `.env`.

The repository `.gitignore` excludes credentials, virtual environments, Python caches, SQLite databases, generated evaluation results, and the full evaluation datasets.

## 6. Verify the Installation

Run:

```bash
python -m cloudserve_support
```

Expected output:

```text
CloudServe Support System - environment OK
```

Run the automated test suite:

```bash
pytest -q
```

The test suite covers normalization, classification, retrieval, routing, guardrails, persistent logging, evaluation, and pipeline behavior.

## 7. Input Data

The system accepts ticket data through an input JSON file.

A ticket contains fields such as:

```json
{
  "ticket_id": "DEV-0001",
  "channel": "chat",
  "subject": "",
  "body": "builds that work last week are now fail during dependency resolution.",
  "received_at": "2026-05-23T22:43:00Z",
  "customer_tier": "standard",
  "customer_region": "latin_america",
  "language_fluency": "non_fluent",
  "must_not_auto_respond": false
}
```

Supported channels include:

* email
* chat
* documentation comments
* forum

The normalization component converts all supported channels into the same internal ticket representation.

The repository contains `data/sample_tickets.json` as a small sanitized example.

The original supplied development, validation, and ground-truth datasets are kept outside the public source repository and can be supplied to the evaluation harness by path.

## 8. Controlled Documentation

`data/documentation.json` contains the controlled support documentation used by the retrieval and response-generation components.

Documents contain:

* document identifier
* title
* category
* applicability
* content
* related documentation
* review metadata

Documents are split into section-aware chunks before embedding.

Short sections remain intact. Longer sections are split into overlapping character windows so that relevant context is retained across chunk boundaries.

Each retrieved chunk retains its document identifier and chunk identifier.

## 9. Classification

Every normalized ticket is classified into:

* one supported intent;
* one urgency category;
* one numeric confidence value between 0 and 1.

The classifier uses a structured output format.

The supported intent set contains 22 categories, including:

```text
account_access
api_key_issue
api_usage_question
authentication_failure
billing_query
compliance_request
configuration_help
data_export
data_residency
database_issue
deployment_failure
feature_request
integration_help
onboarding
performance_degradation
quota_or_overage
rate_limit
rollback_request
security_incident
sso_configuration
...
```

The classifier validates the model output before it is accepted.

Malformed output does not terminate the overall ticket workflow. A fallback classification is recorded when the provider cannot produce a valid classification.

The classifier prompt is versioned in:

```text
prompts/PR-01_classifier_v1.txt
```

## 10. Controlled Documentation Retrieval

Retrieval uses Sentence Transformers embeddings with:

```text
all-MiniLM-L6-v2
```

The embedding dimension is 384.

The system retrieves the top `RETRIEVAL_TOP_K` results and applies a relevance threshold.

The current relevance threshold is:

```text
0.28
```

This threshold was selected from the observed score distribution on the supplied ground-truth set. It preserves the observed minimum score for correct retrieved documentation while allowing retrieval to return no results when content is not sufficiently relevant.

Retrieval can therefore legitimately return zero results.

A retrieval result contains:

* document ID
* chunk ID
* source information
* relevance score
* retrieved content

The system does not use an always-return fallback document.

## 11. Deterministic Routing

Routing is independent of generated response content.

The configured classification confidence threshold is:

```text
0.80
```

A ticket is escalated when any applicable escalation condition is true, including:

* sensitive intent;
* `must_not_auto_respond` is true;
* classification confidence is below the configured threshold;
* controlled documentation is insufficient;
* the response provider fails;
* response generation produces invalid output;
* a generated response is blocked by guardrails.

Sensitive intents include:

* security incidents
* compliance requests
* data residency
* billing queries
* data export

The routing decision contains:

```text
route
reason
```

This makes routing auditable and prevents a generated response from overriding a safety decision.

## 12. Grounded Response Generation

Automatic responses are generated only after the ticket has passed routing requirements and relevant controlled documentation has been retrieved.

The response generator receives:

* normalized ticket;
* classification;
* urgency;
* confidence;
* retrieved documentation;
* applicable safety rules.

The generated response must:

* use the supplied controlled documentation;
* include source references;
* contain the machine-generated disclosure;
* avoid unsupported claims;
* avoid inventing policies, fixes, timelines, refunds, or commitments;
* treat customer-provided text as untrusted input.

When the documentation does not support an answer, the ticket is escalated rather than filled with an unsupported response.

The response prompt is versioned in:

```text
prompts/PR-02_grounded_response_v1.txt
```

## 13. Guardrails

Every generated response is validated before it can be returned to the customer.

The validator checks:

* response structure;
* grounding flag;
* machine-generated disclosure;
* source references;
* source-reference validity;
* whether cited sources were actually retrieved;
* private-data patterns;
* required safety conditions.

The current private-data checks include patterns for:

* email addresses;
* telephone numbers;
* API keys.

A response that fails validation is blocked and routed to human support.

Guardrail validation is therefore a separate enforcement boundary from response generation.

## 14. Persistent Decision Logging

Every processed ticket produces a persistent decision record.

The SQLite decision log records information including:

```text
ticket_id
intent
urgency
confidence
route
routing reason
retrieved document IDs
```

The database is intentionally excluded from Git using:

```text
storage/*.db
```

Decision logging occurs for both successful automated processing and escalation paths.

This ensures that failures and escalations are not invisible to later audit or evaluation.

## 15. Error Handling

The system is designed to continue processing when an individual ticket encounters an expected failure.

Handled conditions include:

* malformed input;
* empty ticket content;
* malformed LLM classification output;
* LLM provider failure;
* empty provider response;
* invalid generated response;
* guardrail failure;
* no relevant documentation.

Provider failures result in a controlled fallback/escalation rather than termination of the complete evaluation run.

The evaluation harness records individual failures and continues processing remaining tickets.

## 16. Evaluation

The evaluation CLI accepts input paths rather than relying on a hardcoded validation filename.

Basic usage:

```bash
python -m cloudserve_support.evaluate \
  --tickets <tickets.json> \
  --documents data/documentation.json \
  --output <results.json>
```

With ground truth:

```bash
python -m cloudserve_support.evaluate \
  --tickets <tickets.json> \
  --documents data/documentation.json \
  --ground-truth <ground_truth.json> \
  --output <results.json>
```

The repository also provides:

```bash
evaluation/harness/run_evaluation.sh
```

Example:

```bash
./evaluation/harness/run_evaluation.sh \
  <tickets.json> \
  data/documentation.json \
  <ground_truth.json> \
  <results.json>
```

The harness processes the supplied evaluation set unattended.

It does not depend on a hardcoded filename.

## 17. Evaluation Metrics

The evaluation records the required metrics, including:

### Volume

* total tickets
* completed tickets
* failed tickets
* completion rate
* answered tickets
* escalated tickets
* guardrail-blocked tickets

### Business metrics

* first-contact-resolution information where available
* mean response/processing time
* median response/processing time
* escalation rate

### Technical metrics

* intent accuracy where ground truth is available
* classification precision/recall by class where applicable
* retrieval Recall@5
* source-reference validity
* required-mention compliance
* must-not-claim compliance
* mean latency
* median latency
* p95 latency

### Governance metrics

* decision-log coverage
* guardrail activations
* private-data detections
* escalation reasons

## 18. Evaluation Evidence

The following measurements were obtained from an earlier run of the supplied 200-ticket ground-truth evaluation set. The run completed successfully with the model provider available; subsequent runs may differ because provider availability and LLM output are nondeterministic.

### Ground-truth evaluation

```text
Tickets:                 200
Completed:               200
Failed:                    0
Completion rate:       100.0%

Intent accuracy:        73.5%
Retrieval Recall@5:     95.0%
Source-reference validity: 100.0%
Required-mention compliance: 75.8%
Must-not-claim compliance: 100.0%

Mean latency:       5222.47 ms
Median latency:     3496.77 ms
P95 latency:       13636.76 ms
```

The results are measured observations from this evaluation run, not guarantees about future runs. LLM-based classification and response generation can exhibit nondeterministic behavior.

### Validation evaluation

The supplied 80-ticket validation set was processed successfully:

```text
Tickets:                 80
Completed:               80
Failed:                    0
Completion rate:       100.0%

Mean latency:       3607.94 ms
Median latency:     2799.26 ms
P95 latency:        8322.44 ms
```

The evaluation results are intentionally excluded from the source repository. They can be regenerated using the evaluation harness.

## 19. Retrieval Evaluation Evidence

On the 200-ticket ground-truth set:

```text
Correct documentation found in top 5: 190 / 200
Recall@5:                              95.0%
```

For the tickets where the expected documentation was retrieved in the top five, the minimum observed correct-document score was approximately:

```text
0.2899
```

The selected relevance threshold of `0.28` therefore retains the observed correct-document boundary with a small margin.

However, the score distributions overlap: a high similarity score does not by itself guarantee that a document is the correct authoritative source. Source grounding and routing remain separate controls.

## 20. Reproducibility

From a clean checkout:

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .
cp .env.example .env
```

Configure the required API key and run:

```bash
pytest -q
```

Then run an evaluation with explicit input and output paths:

```bash
python -m cloudserve_support.evaluate \
  --tickets <tickets.json> \
  --documents data/documentation.json \
  --output <results.json>
```

For a ground-truth evaluation:

```bash
python -m cloudserve_support.evaluate \
  --tickets <tickets.json> \
  --documents data/documentation.json \
  --ground-truth <ground_truth.json> \
  --output <results.json>
```

The complete supplied evaluation set can therefore be processed without manual intervention.

## 21. Automated CI

GitHub Actions is configured in:

```text
.github/workflows/ci.yml
```

The CI workflow:

1. checks out the repository;
2. installs Python 3.14;
3. installs pinned dependencies;
4. executes the pytest suite.

The workflow does not require the private OpenRouter API key because the automated unit tests do not depend on live provider access.

## 22. Security and Data Handling

The repository is intentionally structured to avoid committing secrets and evaluation data.

Excluded files include:

```text
.env
.venv/
*.pyc
.pytest_cache/
storage/*.db
storage/*.json
evaluation/results/*.json
data/development_tickets.json
data/validation_tickets.json
data/ground_truth_tickets.json
data/ground_truth_responses.json
src/cloudserve_support.egg-info/
```

The public/sample repository contains:

* controlled documentation;
* sanitized sample tickets;
* source code;
* tests;
* prompts;
* evaluation harness;
* architecture documentation.

The full supplied evaluation datasets remain outside source control.

## 23. Safety Boundary

The system does not treat the LLM as the final authority for whether a customer request can be answered automatically.

The safety boundary is implemented through:

```text
Classification
      |
      v
Deterministic Routing
      |
      v
Controlled Documentation
      |
      v
Grounded Response Generation
      |
      v
Guardrail Validation
      |
      v
Customer Response OR Human Escalation
```

This separation provides independent controls for:

* uncertainty;
* sensitive requests;
* unsupported documentation;
* provider failures;
* malformed responses;
* private-data leakage;
* untrusted customer instructions.

## 24. Known Limitations

The current implementation has several measurable limitations.

### Classification accuracy

The ground-truth evaluation produced an intent accuracy of `73.5%`. This indicates that classification remains an area for improvement.

### Required-mention compliance

Required-mention compliance was `75.8%`. Some generated responses therefore did not include every expected phrase or concept from the reference evaluation.

### Retrieval

Retrieval Recall@5 was `95.0%`, meaning that 10 of the 200 ground-truth tickets did not have their expected documentation in the top five retrieved results.

### Latency

The measured ground-truth median latency was approximately `3.50 seconds`, with a p95 of approximately `13.64 seconds`.

### LLM nondeterminism

Provider-generated classification and response output can vary between runs. Consequently, individual evaluation metrics can change between runs.

These limitations are reported explicitly rather than hidden by selecting only successful examples.

## 25. Design Principles

The implementation follows these principles:

1. **Normalize first** — downstream processing operates on one ticket representation.
2. **Classify explicitly** — intent, urgency, and confidence are structured outputs.
3. **Retrieve only controlled documentation** — private agent-answer files are not authoritative.
4. **Route deterministically** — safety routing does not depend on generated response wording.
5. **Generate only when supported** — insufficient evidence results in escalation.
6. **Validate every generated response** — generation is not itself a safety decision.
7. **Log every decision** — success and failure paths are auditable.
8. **Fail closed for sensitive cases** — uncertainty and safety indicators lead to human review.
9. **Evaluate unattended** — the evaluation harness processes the supplied set without manual intervention.
10. **Measure rather than assume** — reported performance numbers come from explicit evaluation runs.

## 26. Prompt Library

The versioned prompts are stored under `prompts/`.

### PR-01 — Classifier

```text
prompts/PR-01_classifier_v1.txt
```

Defines intent and urgency classification behavior, boundaries, structured output requirements, and confidence handling.

### PR-02 — Grounded Response

```text
prompts/PR-02_grounded_response_v1.txt
```

Defines evidence-grounded response generation, citation requirements, disclosure, unsupported-claim restrictions, and treatment of customer content as untrusted.

### PR-03 — Evaluator

```text
prompts/PR-03_evaluator_v1.txt
```

Contains the evaluation-oriented prompt artifact developed during the prompt-library stage. The production evaluation harness currently uses deterministic metric calculation rather than relying on an LLM evaluator for the reported metrics.

## 27. Architecture Documentation

Detailed architecture documentation is available at:

```text
docs/architecture/architecture.md
```

It documents:

* end-to-end processing;
* component responsibilities;
* safety boundaries;
* configuration;
* evaluation architecture;
* failure handling;
* design principles.

## 28. Attribution

The implementation uses third-party open-source libraries and model services documented through the project's dependency and configuration files.

Substantive AI-assisted implementation work is disclosed as part of the capstone submission. AI assistance was used for coding, debugging, prompt drafting, library/API explanations, and implementation review. Discovery findings, problem framing, evaluation interpretation, and personal reflection remain the student's own work.

## 29. Clean-Checkout Requirement

The repository is intended to be executable from a clean checkout.

An evaluator should be able to:

1. clone the repository;
2. create a Python 3.14 environment;
3. install `requirements.txt`;
4. install the project;
5. configure the required provider key;
6. run the test suite;
7. provide evaluation input and documentation paths;
8. run the evaluation harness;
9. inspect the resulting metrics and decision logs.

No hardcoded local path is required for evaluation input.

## 30. License

This repository is a course capstone implementation for CloudServe Solutions.

Where third-party libraries, models, or services are used, their respective licenses and terms apply.

