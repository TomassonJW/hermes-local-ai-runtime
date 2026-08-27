# API and job model

## Dual surface

Native `/api/v1` is normative for capabilities, async jobs, evidence, warnings, policies, media/documents, model/evaluation lifecycle.

OpenAI-compatible `/v1` serves Hermes/ecosystem and translates into native jobs/routes. It is not the internal domain model. Candidate endpoints: chat completions, responses, embeddings, rerank, audio transcriptions and models.

## Request envelope

```json
{
  "capability": "vision.analyze",
  "capability_version": "1",
  "profile": "balanced",
  "input": {"question": "What error is visible?", "media": [{"upload_id": "upl_..."}]},
  "policy": {"data_classification": "confidential", "cloud_fallback_allowed": false, "retention": "none"},
  "constraints": {"timeout_ms": 60000}
}
```

## Result envelope

```json
{
  "job_id": "job_...",
  "status": "succeeded",
  "result": {"answer": "…"},
  "review_required": false,
  "evidence": [],
  "warnings": [],
  "provenance": {"capability": "vision.analyze@1", "route": "vision-balanced@2026-08", "engine": "llama.cpp", "model_artifacts": ["sha256:…"], "preset": "vision-balanced-cpu-v1"},
  "timing": {"queued_ms": 0, "load_ms": 3200, "inference_ms": 8400}
}
```

## Sync/async

Sync only if route permits, input under threshold, queue within budget, expected duration and client timeout fit. Otherwise 202 + job location. Audio, multipage docs, downloads and evaluations are async.

## Idempotency/cancellation

Mutating submit accepts scoped `Idempotency-Key`; same key different payload is error. Cancellation removes queued, aborts load when safe, signals/terminates isolated running worker per policy and prevents publication where safe.

## Uploads

Bounded upload stream validates size/hash and returns upload ID; job references it; retention deletes. No arbitrary server paths or remote URLs initially.

## Errors

Stable codes include invalid/unsupported/too large, capability unavailable, route unapproved, resource/queue, timeout/cancel, load/worker crash, schema failure, policy/licence denial and internal error. See `contracts/error-catalog.md`.
