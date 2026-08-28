# Error catalogue

| Code | HTTP | Retryable | Meaning |
| --- | ---: | --- | --- |
| `INVALID_INPUT` | 400 | no | Request/schema invalid |
| `UNSUPPORTED_MEDIA` | 415 | no | Media unsupported |
| `INPUT_TOO_LARGE` | 413 | after reduction | Route limit exceeded |
| `CAPABILITY_UNAVAILABLE` | 503 | maybe | No approved installed route |
| `ROUTE_NOT_APPROVED` | 503 | no | Candidate route without scope |
| `POLICY_DENIED` | 403 | no | Consumer/data/fallback denied |
| `AUTH_REQUIRED` | 401 | no | Identity absent/invalid |
| `SCOPE_DENIED` | 403 | no | Scope absent |
| `RESOURCE_EXHAUSTED` | 503 | yes | Safe admission impossible |
| `QUEUE_FULL` | 429 | yes | Bounded queue full |
| `TIMEOUT` | 504 | maybe | Deadline exceeded |
| `CANCELLED` | 409 | maybe | Job cancelled |
| `MODEL_LOAD_FAILED` | 503 | maybe | Worker/model not ready |
| `WORKER_CRASHED` | 503 | maybe | Worker exited |
| `OUTPUT_SCHEMA_FAILED` | 422 | maybe | Output invalid/repair failed |
| `OUTPUT_TOO_LARGE` | 422 | no | Result exceeds the configured byte limit |
| `LOW_CONFIDENCE` | 422 | after review | Route abstained |
| `LICENCE_BLOCKED` | 451 | no | Artefact unauthorised |
| `IDEMPOTENCY_CONFLICT` | 409 | no | Key reused for different payload |
| `RESULT_NOT_READY` | 409 | yes | Job exists but has no immutable result yet |
| `NOT_FOUND` | 404 | no | Resource absent/invisible |
| `INTERNAL_ERROR` | 500 | maybe | Unexpected control-plane failure |

Errors include stable code, message, retryability, request ID, optional retry-after/details. Details never expose another consumer, private path, secret or payload.
