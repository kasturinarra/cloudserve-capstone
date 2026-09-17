# CloudServe Solutions — System Architecture

## 1. Overview

CloudServe Solutions is an intelligent customer support system that processes support requests from multiple channels, classifies the request, retrieves relevant information from controlled documentation, determines whether the ticket can be answered automatically, generates a grounded response when appropriate, validates the response with guardrails, and persistently records the processing decision.

The system is designed around a safety-first boundary:

- Classification determines intent, urgency, and confidence.
- Deterministic routing decides whether automatic response is permitted.
- Automatic responses require supporting content from controlled documentation.
- Generated responses are validated before being returned to the customer.
- Tickets that are sensitive, uncertain, unsupported, or blocked by a guardrail are escalated to human support.
- Every processed ticket produces a persistent decision record.

---

## 2. End-to-End Processing Flow

```text
+----------------------+
| Ticket Input         |
| Email / Chat / Docs  |
| Comments / Forum     |
+----------+-----------+
           |
           v
+----------------------+
| Ticket Normalization |
+----------+-----------+
           |
           v
+----------------------+
| Classification       |
| Intent               |
| Urgency              |
| Confidence           |
+----------+-----------+
           |
           v
+----------------------+
| Deterministic        |
| Routing              |
+----------+-----------+
           |
      +----+----+
      |         |
  escalate   auto-respond
      |         |
      |         v
      |  +----------------------+
      |  | Controlled           |
      |  | Documentation        |
      |  | Retrieval            |
      |  | Top-K + Threshold    |
      |  +----------+-----------+
      |             |
      |        +----+----+
      |        |         |
      |    no relevant  relevant
      |     documents   documents
      |        |         |
      |        |         v
      |        |  +----------------------+
      |        |  | Response Generation  |
      |        |  | Grounded + Citations |
      |        |  +----------+-----------+
      |        |             |
      |        |             v
      |        |  +----------------------+
      |        |  | Guardrail Validation |
      |        |  +----------+-----------+
      |        |             |
      |        |        +----+----+
      |        |        |         |
      |        |      block      pass
      |        |        |         |
      +--------+--------+         |
               |                  |
               v                  v
        +-------------+     +-------------+
        | Human       |     | Customer    |
        | Support     |     | Response    |
        +------+------+     +------+------+
               |                   |
               +---------+---------+
                         |
                         v
                +----------------------+
                | Persistent Decision  |
                | Log                  |
                | SQLite               |
                +----------------------+
The flow has two principal outcomes:

Customer response — when the ticket passes deterministic routing, has sufficient controlled documentation support, and the generated response passes guardrail validation.
Human escalation — when the ticket is sensitive, must not be automatically answered, has insufficient classification confidence, has no sufficient documentation support, or the generated response is blocked by a guardrail.
## 3. Main Components
### 3.1 Ticket Normalization

The normalization component converts incoming support requests into a common internal representation.

Supported input channels are:

Email
Chat
Documentation comments
Forum channels

The normalized ticket contains:

ticket_id
channel
subject
body
received_at
Customer metadata when available
must_not_auto_respond

The normalized representation allows downstream components to operate independently of the original channel.

### 3.2 Classification

The classifier determines:

Intent
Urgency
Confidence

The system uses a controlled set of supported intent categories and urgency categories.

The returned confidence is numeric and bounded between 0 and 1.

The classifier uses a structured JSON response format. Malformed model output is handled rather than being allowed to terminate the complete ticket-processing workflow.

When the LLM provider cannot provide a usable classification, the system falls back to an unclear_request classification with low confidence so that deterministic routing can escalate the ticket.

This provides a safe failure mode rather than assuming that an unavailable or malformed model response is correct.

### 3.3 Controlled Documentation Retrieval

For tickets eligible for automatic response, the system searches the supplied controlled support documentation.

The retrieval pipeline consists of:

Loading the approved documentation.
Splitting documentation into structured chunks.
Generating embeddings for the chunks.
Embedding the ticket query.
Computing similarity between the query and documentation chunks.
Returning the highest-ranked relevant passages.
Applying a relevance threshold.

The implementation uses the all-MiniLM-L6-v2 embedding model and 384-dimensional embeddings.

The retrieval component returns identifiable documentation information including:

Document ID
Document title
Chunk information
Content
Relevance score

The configured relevance threshold is 0.28.

The threshold was selected using the observed retrieval-score distribution from the supplied ground-truth evaluation set. The observed minimum score for a correct document appearing in the top five was approximately 0.2899, while the threshold was set slightly below this value to avoid unnecessarily removing observed relevant results.

The retriever is allowed to return no results.

A ticket with no sufficiently relevant documentation is escalated rather than answered using unsupported information.

### 3.4 Deterministic Routing

Routing is implemented independently from response generation.

The routing decision considers:

Ticket intent
Classification confidence
Must-not-auto-respond indicators
Sensitive intent categories
Retrieval availability
Defined safety and routing rules

Sensitive intents include:

security_incident
compliance_request
data_residency
billing_query
data_export

Tickets are escalated when:

The ticket is marked must_not_auto_respond.
The ticket belongs to a sensitive intent category.
Classification confidence is below the configured threshold.
Sufficient supporting documentation cannot be retrieved.
Response generation fails.
Guardrail validation blocks the generated response.

The current confidence threshold is 0.80.

The routing component produces a structured decision:

route = auto-respond | human
reason = explanation of routing decision

The response generator cannot override the routing decision.

### 3.5 Grounded Response Generation

Eligible tickets are passed to the response-generation component together with the retrieved controlled documentation.

The response-generation prompt requires the model to:

Use the supplied documentation as the evidence base.
Avoid unsupported claims.
Avoid inventing policies, fixes, timelines, refunds, or commitments.
Treat the customer-provided ticket content as untrusted input.
Return only source references corresponding to retrieved documentation.
Indicate when the available documentation is insufficient.
Include the required machine-generated disclosure.

The generated response has a structured representation containing:

Customer-facing response
Source references
Machine-generated disclosure
Grounded status

The system therefore separates customer-provided information from system instructions and controlled documentation.

### 3.6 Guardrail Validation

Every generated response is validated before it can be returned to the customer.

The guardrail validation checks:

Whether the response is marked as grounded.
Whether the required disclosure is present.
Whether source references are present.
Whether source references correspond to documents actually retrieved for the ticket.
Whether private or sensitive information patterns are present.
Whether the generated response violates the response-generation constraints.

The implementation includes detection patterns for information such as:

Email addresses
Phone numbers
API keys

A guardrail failure prevents the generated response from being returned to the customer.

Instead, the ticket is escalated to human support and the decision is persisted in the decision log.

This creates the following safety boundary:

Generated Response
       |
       v
Guardrail Validation
       |
   +---+---+
   |       |
 block    pass
   |       |
   v       v
Human    Customer
Support  Response
### 3.7 Persistent Decision Logging

The system maintains a persistent SQLite decision log.

Every processed ticket creates a decision record containing:

Ticket identifier
Intent
Urgency
Confidence
Routing decision
Routing reason
Retrieved documentation identifiers where applicable

The decision log is persistent across individual processing requests.

The log is intended to support:

Auditability
Debugging
Evaluation
Reconciliation between processed tickets and evaluation results
Investigation of escalation and guardrail decisions

Processing failures are also converted into controlled outcomes where possible so that an individual ticket does not silently disappear from the evaluation.

### 3.8 Evaluation

The evaluation system is implemented as an unattended command-line harness.

The harness accepts:

Ticket input path
Documentation input path
Optional ground-truth input path
Output path

This avoids dependence on a hardcoded validation filename.

The evaluation processes the complete supplied dataset and records per-ticket processing results.

The evaluation calculates metrics including:

Total tickets
Completed tickets
Failed tickets
Completion rate
Intent accuracy
Retrieval Recall@5
Source-reference validity
Required-mention compliance
Must-not-claim compliance
Mean latency
Median latency
P95 latency
Failure counts

The evaluation continues processing remaining tickets when an individual ticket encounters a controlled failure.

## 4. Safety Boundary

The architecture deliberately separates model generation from authorization to answer.

The model does not decide whether a ticket should be answered automatically.

The system first applies deterministic routing rules.

For automatically answerable tickets, controlled documentation must provide supporting evidence.

The generated answer is then validated by guardrails.

The resulting control boundary is:

                 +----------------+
                 | Classification |
                 +-------+--------+
                         |
                         v
                +------------------+
                | Deterministic    |
                | Routing           |
                +--------+---------+
                         |
                 +-------+-------+
                 |               |
              escalate       auto-response
                 |               |
                 v               v
             Human       Documentation
             Support      Retrieval
                              |
                         +----+----+
                         |         |
                       none     support
                         |         |
                         v         v
                      Human    Response
                      Support  Generation
                                   |
                                   v
                              Guardrails
                                   |
                              +----+----+
                              |         |
                            block      pass
                              |         |
                              v         v
                           Human     Customer
                           Support   Response

This boundary prevents response generation from bypassing routing, retrieval, or validation controls.

## 5. Configuration

The system configuration is provided through environment variables.

Important configuration values include:

OPENROUTER_API_KEY
MODEL_NAME
EMBEDDING_MODEL
CHROMA_PATH
DATABASE_URL
LOG_LEVEL
CONFIDENCE_THRESHOLD
RETRIEVAL_TOP_K

The current configuration uses:

MODEL_NAME=meta-llama/llama-3.1-8b-instruct
EMBEDDING_MODEL=all-MiniLM-L6-v2
CONFIDENCE_THRESHOLD=0.80
RETRIEVAL_TOP_K=5

Secrets are stored in .env and excluded from version control.

The repository contains .env.example with placeholder configuration values.

## 6. Evaluation Architecture

The evaluation architecture separates the processing pipeline from the evaluation harness.

+-------------------------+
| Evaluation Dataset      |
+------------+------------+
             |
             v
+-------------------------+
| Evaluation Harness      |
| run_evaluation.sh       |
+------------+------------+
             |
             v
+-------------------------+
| CloudServe Pipeline     |
+------------+------------+
             |
             v
+-------------------------+
| Per-ticket Results      |
+------------+------------+
             |
             v
+-------------------------+
| Evaluation Results JSON  |
+------------+------------+
             |
             v
+-------------------------+
| Analysis / Summary      |
+-------------------------+

The harness can be executed with different input files, allowing the same implementation to be evaluated against both the supplied validation dataset and other evaluation datasets.

### 6.1 Validation Evaluation Evidence

The latest validation evaluation processed:

Total tickets: 80
Completed: 80
Failed: 0
Completion rate: 100%

Latency measurements:

Mean latency: 3607.94 ms
Median latency: 2799.26 ms
P95 latency: 8322.44 ms

The validation run completed without an individual ticket failure.

### 6.2 Ground-Truth Evaluation Evidence

The latest ground-truth evaluation processed:

Total tickets: 200
Completed: 200
Failed: 0
Completion rate: 100%

Measured results:

Intent accuracy: 73.5%
Retrieval Recall@5: 95.0%
Source-reference validity: 100%
Required-mention compliance: 75.8%
Must-not-claim compliance: 100%

Latency measurements:

Mean latency: 5222.47 ms
Median latency: 3496.77 ms
P95 latency: 13636.76 ms

These results represent the latest completed ground-truth evaluation run.

## 7. Repository-Level Evaluation Artifacts

The evaluation-related repository structure is:

evaluation/
├── analysis/
│   └── summarize_results.py
├── harness/
│   └── run_evaluation.sh
└── results/
    ├── evaluation_results.json
    └── ground_truth_evaluation.json

The harness provides a reproducible entry point for processing an evaluation dataset.

The summary script reads an evaluation result file and prints the main metrics in a compact form.

## 8. Failure Handling

The system is designed to degrade safely when individual processing components fail.

8.1 Malformed Classification Output

If the classifier returns malformed output, the system retries once.

If a usable result still cannot be obtained, the system uses a safe fallback classification with low confidence.

The low confidence causes deterministic routing to escalate the ticket.

8.2 LLM Provider Failure

LLM provider errors are converted into controlled workflow outcomes.

A provider failure does not cause the complete evaluation run to terminate.

The affected ticket is routed to human handling and the decision is logged.

8.3 No Retrieval Result

The retriever can return no relevant documentation.

The system does not manufacture an answer in this situation.

The ticket is escalated to human support.

8.4 Guardrail Failure

If a generated response fails guardrail validation, the response is blocked.

The ticket is converted to a human-support escalation and the routing decision is persisted.

The blocked response is not returned to the customer.

8.5 Individual Ticket Failure

The evaluation harness processes tickets independently.

A controlled failure for one ticket should not silently terminate evaluation of the remaining dataset.

The evaluation records failure information so that the final results can be reconciled.

## 9. Design Principles

The architecture follows these principles:

9.1 Safety Before Automation

Automatic response is allowed only after routing, documentation retrieval, response generation, and guardrail validation requirements are satisfied.

9.2 Controlled Evidence

Customer responses are grounded in the supplied controlled documentation rather than unrestricted model knowledge.

9.3 Deterministic Routing

The LLM does not determine whether it is authorized to answer a ticket.

Routing is performed by explicit system rules.

9.4 Fail Closed

When confidence is insufficient, documentation is unavailable, a provider fails, or a guardrail blocks a response, the system escalates rather than inventing an answer.

9.5 Persistent Auditability

Every processed ticket has a persistent decision record so that automated decisions can be reviewed after processing.

9.6 Reproducible Evaluation

Evaluation is performed through a documented command-line harness that accepts explicit input and output paths.

9.7 Separation of Concerns

The implementation separates:

Input normalization
Classification
Retrieval
Routing
Response generation
Guardrail validation
Decision logging
Evaluation

This separation allows individual components to be tested and reasoned about independently while preserving a complete end-to-end workflow.

