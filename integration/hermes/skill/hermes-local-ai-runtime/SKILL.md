---
name: hermes-local-ai-runtime
description: Use the shared local AI runtime from Hermes.
version: 0.1.0
author: Thomas Jankowski, Hermes Agent
license: Apache-2.0
platforms: [linux]
metadata:
  hermes:
    tags: [local-ai, inference, vision, ocr, embeddings, audio]
    category: mlops
---

# Hermes Local AI Runtime Skill

Use this skill when Hermes must consume or integrate the shared local AI runtime. It selects capabilities, not model files, and preserves application data ownership. It does not install models, change routes, or bypass runtime limits.

## When to Use

Load this skill when:

- a Hermes application needs OCR, document parsing, structured extraction, embeddings, reranking, vision, object/image analysis, or transcription;
- Hermes should use a local auxiliary vision endpoint;
- a developer asks which local capability is available;
- an existing consumer must migrate away from a hardcoded model server;
- a local AI request fails and route, policy, resource, or review state must be diagnosed.

Do not load it merely to discuss AI models in general.

## Prerequisites

- the runtime is installed and reachable through its authorised local/private endpoint;
- the consumer has a scoped credential when required;
- capability discovery is available;
- the consumer's data classification and fallback policy are known;
- any state-changing model or route operation has operator approval.

## How to Run

1. Discover the runtime before assuming a capability.
2. Select a capability and profile.
3. Validate input and data policy.
4. Submit through the native API or the approved compatibility surface.
5. Inspect warnings, review state, and provenance.
6. Let the consumer apply business rules and persist results.

Completion means the consumer uses a stable capability contract, handles explicit failures, and contains no checkpoint/runtime flags.

## Quick Reference

| Need | Capability |
| --- | --- |
| answer an image question | `vision.analyze@1` |
| structured fields from image | `vision.extract_structured@1` |
| native PDF text | `document.text_extract@1` |
| OCR | `document.ocr@1` |
| layout/tables | `document.parse@1` |
| structured document fields | `document.extract_structured@1` |
| text JSON extraction | `text.extract_structured@1` |
| semantic vectors | `text.embed@1` |
| reorder candidates | `search.rerank@1` |
| transcribe audio | `audio.transcribe@1` |

Profiles:

- `fast`: smallest approved route;
- `balanced`: default;
- `accurate`: strongest approved local route.

`accurate` never implies cloud.

## Procedure

### 1. Discover

Call the runtime's system and capability discovery endpoints or its configured MCP tools.

Verify:

- capability/version exists;
- route is currently available;
- media and size limits;
- sync versus async;
- data-class maximum;
- profile support.

If unavailable, report the exact state. Do not launch a separate unmanaged model server.

### 2. Choose the surface

Use the native capability API for documents, jobs, evidence, and specialised operations.

Use the OpenAI-compatible endpoint when Hermes model/auxiliary configuration requires it.

Use MCP/tools for explicit specialised actions exposed as tools.

### 3. Preserve the data boundary

The consumer:

- retrieves database candidates;
- submits only the bounded data required;
- receives scores/results;
- validates and writes.

Never give the runtime general database credentials or ask it to mutate business data.

### 4. Submit policy

Set:

- data classification;
- profile;
- timeout;
- retention;
- cloud fallback, normally false;
- human review requirements.

Do not pass arbitrary engine flags. Operator-only model override is for benchmarks and debugging.

### 5. Handle outcomes

Treat these as normal:

- queued;
- resource rejected;
- unsupported media;
- low confidence;
- review required;
- output schema failure;
- cancelled;
- capability unavailable.

Do not hide them with recursive retries.

### 6. Verify result

Inspect:

- schema or expected result type;
- evidence and warnings;
- `review_required`;
- capability/route/model/preset provenance;
- transformations;
- cache and timing.

The model's own confidence is not sufficient evidence.

### 7. Integrate tests

A consumer integration includes:

- synthetic success;
- invalid input;
- unavailable capability;
- resource rejection;
- review-required result;
- timeout/cancellation where asynchronous;
- no model-specific configuration in consumer code.

## Vision Rules

A small local VLM is useful but not universally equivalent to frontier vision.

Prefer:

1. native/deterministic extraction;
2. OCR or specialised detector/embedding;
3. local VLM;
4. human review or explicitly authorised fallback.

For Hermes auxiliary vision with a text-only main model, ask the actual visual question. A generic caption loses task information because the main model does not see the pixels.

## Reranking

Embeddings retrieve a broad candidate set quickly. Reranking reads the query with each top candidate and returns a more precise order. Send a bounded candidate list; do not send the whole database.

## Pitfalls

- hardcoding a model filename in an application;
- treating `accurate` as permission for cloud;
- using a VLM for exact coordinates when a detector exists;
- using model self-confidence as a business threshold;
- starting a second llama.cpp/Ollama instance outside runtime admission;
- storing embeddings in the runtime instead of the consumer;
- logging confidential payloads;
- retrying a resource refusal until the server is overloaded.

## Verification

The use is correct when:

- capability discovery preceded invocation;
- the consumer owns persistence and decisions;
- explicit policy accompanied the request;
- failures and review state are handled;
- provenance is retained as needed;
- no model/engine details leaked into the consumer contract;
- no unauthorised external request occurred.
