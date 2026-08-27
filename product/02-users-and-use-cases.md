# Users and use cases

## Primary users

### Hermes as software builder

Hermes needs a canonical way to add local AI without choosing models and rebuilding infrastructure in every repository. It discovers capabilities, reads contracts, selects a profile, creates a thin adapter and tests with synthetic fixtures.

### Application developer

Needs typed HTTP/SDK calls, bounded execution, provenance and explicit failure modes.

### Operator

Needs to know what is running, loaded, queued, failing, under pressure, outdated, unlicensed or reversible.

### Product reviewer

Thomas needs a clear console that exposes value/trade-offs without routine manipulation of temperature, KV cache, tensor split or engine flags.

## Core use cases

### Hermes auxiliary vision

A text-only main model delegates image plus actual question to a local route. The runtime returns a task-specific answer, provenance, limitations and review status.

### Native multimodal main model

A future local multimodal main model is served through the runtime's OpenAI-compatible endpoint so pixels remain available to the main model.

### Document intake

Check native text; preprocess image pages; OCR/layout; use VLM only for missing/ambiguous fields; validate JSON schema; return evidence/warnings. The application persists only after its own rules and confirmation.

### Structured extraction

Given text/image plus a schema, return typed JSON rather than prose, with nulls, evidence, warnings and route provenance.

```json
{
  "document_type": "invoice",
  "supplier_name": "Example Energy",
  "issue_date": "2026-08-20",
  "total_amount": 123.45,
  "currency": "EUR",
  "review_required": true
}
```

### Embedding

Return vectors with model/revision, dimensions, normalisation and compatibility metadata. The consumer stores/indexes them.

### Reranking

A fast first search retrieves plausible candidates; the reranker reads query plus each top candidate and reorders them more precisely. Example: retrieve fifty possible suppliers, then put the correct legal entity above similar names before user confirmation.

### Object and image analysis

Object detection, image embedding, similarity, duplicate detection and classification use specialists; a VLM may provide semantic second pass.

### Speech transcription

Bounded batch job with VAD, chunking, timestamps, language, cancellation and provenance, without payload logs.

### Model evaluation

Compare candidate quality, latency, memory, failure and licence before promotion.

### Future coding/main model

A future GPU worker hosts a larger model under unchanged capability/compatibility contracts.

## Excluded journeys

Generic chat as main UI; runtime database writes; arbitrary engine flags for applications; automatic newest-model promotion; private material in public reports.
