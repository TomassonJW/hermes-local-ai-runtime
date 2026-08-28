---
name: hermes-local-ai-runtime
description: Use when wiring an app to the local AI runtime.
version: 0.2.0
author: Thomas Jankowski, Hermes Agent
license: Apache-2.0
platforms: [linux]
metadata:
  hermes:
    tags: [local-ai, ocr, vision, embeddings, audio, consumers]
    category: mlops
---

# Connect an app to Hermes Local AI Runtime

Hand this skill to any session that must call the shared runtime. The app
speaks HTTP capabilities. It never names a GGUF file, never starts Ollama or
llama.cpp on its own, and never gives the runtime a database credential.

This skill does not install models, enable systemd, or change Hermes
`config.yaml`.

## When to Use

- An application (Sillage or any other) needs OCR, invoice fields, PDF text,
  vision, embeddings, rerank, or batch transcription from the local runtime.
- A coding agent must wire a consumer without knowing this repository's
  internals.

Do not use it to discuss models in general, to download weights, or to expose
the runtime on a public address.

## Reachability

Default control plane (this VM, loopback only):

```text
http://127.0.0.1:8830
```

1. `GET /healthz` must return `{"status":"ok"}` with no auth.
2. Apps use `Authorization: Bearer $HERMES_LOCAL_AI_TOKEN`.
3. The console cookie is for the UI only. Do not use it from Sillage.

If `/healthz` fails, stop. Do not spawn a second inference server.

Completion: health is ok and the token is read from the environment, never
written into Git.

## Discover first

```text
GET /api/v1/capabilities
```

Treat the live list as truth. If a capability is missing, fail explicitly.

Completion: you have the JSON list and you picked an `id` whose `status` is
`available` and whose `profiles` include the profile you will send.

## Capabilities that exist on this deployment

| Need | Capability | Default profile | Input |
| --- | --- | --- | --- |
| Native PDF text | `document.text_extract` | `balanced` | `upload_id` |
| OCR an image/PDF scan | `document.ocr` | `balanced` | `upload_id` |
| Invoice-like fields | `document.extract_structured` | `balanced` | `upload_id` |
| Layout/parse | `document.parse` | `balanced` | `upload_id` |
| Question about an image | `vision.analyze` | `balanced` | `upload_id` + `question` |
| Coloured-box objects | `vision.detect_objects` | `balanced` | `upload_id` |
| Compare two images | `vision.compare` | `fast` | `upload_id` + `upload_id_b` |
| Embed texts | `text.embed` | `balanced` | `texts` or `items` |
| Reorder a short list | `search.rerank` | `balanced` | `query` + `candidates` or `documents` |
| Transcribe a file | `audio.transcribe` | `balanced` | `upload_id` |
| Short local text | `text.generate` | `balanced` | `prompt` |

`text.generate` / `fast` is a dummy echo. Do not use it for product copy.

Not available here: `vision.extract_structured`, streaming ASR, a shared
vector database, cloud fallback.

Timeouts: OCR ~60s, embed/rerank/text ~120s, vision/audio ~180s. The sample
client default of 20s is too short for those jobs.

## Policy (required on every job)

```json
{
  "data_classification": "internal",
  "cloud_fallback_allowed": false,
  "retention": "none"
}
```

Do not set cloud fallback true.

## Call pattern

Reuse `consumers/client.py` when the consumer is Python. Otherwise:

1. Files: `POST /api/v1/uploads` with the raw bytes and the real
   `Content-Type` (`application/pdf`, `image/png`, `audio/wav`, …). Read
   `upload_id`.
2. `POST /api/v1/jobs` with:

```json
{
  "capability": "document.extract_structured",
  "capability_version": "1.0.0",
  "profile": "balanced",
  "input": { "upload_id": "upl_…" },
  "policy": {
    "data_classification": "internal",
    "cloud_fallback_allowed": false,
    "retention": "none"
  }
}
```

3. Poll `GET /api/v1/jobs/{job_id}` until `succeeded`, `failed`,
   `cancelled`, or `rejected`.
4. On success, `GET /api/v1/jobs/{job_id}/result`.
5. The consumer validates, then writes to **its** database.

Text jobs skip upload. Embed:

```json
{ "texts": ["facture 12", "avoir 12"] }
```

Rerank (bounded list from the consumer, never the whole DB):

```json
{
  "query": "facture ACME 123,45 EUR",
  "candidates": [
    { "id": "exp-1", "text": "ACME 123.45" },
    { "id": "exp-2", "text": "other 10.00" }
  ],
  "top_n": 5
}
```

Store returned vectors and `space_id` in the consumer. If `space_id` changes,
re-embed. Do not ask the runtime to keep a vector index.

Completion: one real job reached a terminal status and the consumer persisted
or displayed the result without sending DB secrets.

## Data boundary

The runtime computes. The app owns writes, matching rules, and user
confirmation.

Never:

- send a connection string, token vault, or customer dump;
- log request payloads;
- hardcode a model filename or llama.cpp flag;
- retry a resource rejection in a tight loop;
- treat model confidence as a business decision.

## Reference in this clone

- Contract: `contracts/openapi.yaml`
- Python client: `consumers/client.py`
- Invoice example: `consumers/sillage_app.py`

Pass `timeout_s=180` for vision/audio when using `RuntimeClient.invoke`.

## Common Pitfalls

1. Using the Hub URL from a backend. Apps on this VM call `127.0.0.1:8830`.
2. Using the UI cookie instead of a Bearer token.
3. Assuming `fast` text generation is a real model.
4. Sending the whole Sillage ledger to `search.rerank`.
5. Storing embeddings in the runtime.
6. Hiding `rejected` / `CAPABILITY_UNAVAILABLE` behind a cloud call.

## Verification Checklist

- [ ] `GET /healthz` is ok
- [ ] `GET /api/v1/capabilities` lists the capability you need
- [ ] No model filename in the consumer
- [ ] Policy has `cloud_fallback_allowed: false`
- [ ] Files go through `/api/v1/uploads`
- [ ] Timeouts match the job class
- [ ] Results are persisted only in the consumer
- [ ] Failures surface to the user; no silent retry storm
