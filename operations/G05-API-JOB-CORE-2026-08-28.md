# G-05 API and job core evidence — 2026-08-28

## Verdict

G-05 passes on loopback for the authorised scope. The native capability API,
bounded job core and OpenAI-compatible chat adapter were exercised against the
selected real llama.cpp route. This is source code and test evidence, not a
permanent installation or consumer integration.

## Delivered boundary

- FastAPI control plane under `runtime/`, started only with an explicit YAML
  path and a bearer token resolved from an environment variable.
- Loopback-only listener and loopback-only upstream validation. Non-loopback
  listener or upstream configuration fails closed before startup.
- Native endpoints: health, readiness, system description, capability list,
  submit/status/cancel/result, bounded raw upload and metrics.
- Compatibility endpoints: `/v1/models` and `/v1/chat/completions`.
- Route selection remains capability/profile based; consumer requests cannot
  select checkpoint files, inference engines or engine flags.
- Private SQLite metadata store with schema version, idempotency index, restart
  convergence and consumer isolation. Request and result payloads remain only
  in bounded process memory and disappear at shutdown; they are never persisted
  or logged.
- Native JSON bodies are bounded before model validation and again before queue
  retention. Upstream response bytes, each decoded result and the aggregate
  volatile result store have explicit ceilings.
- Authentication scopes: capability invocation, own-job read/cancel and system
  read. Cross-consumer job existence is hidden, and resolved principal names
  and token values must each be unique.
- Admission before worker start: memory floor, one heavy lease, two light
  leases and queue bound eight.
- Accepted jobs rotate in the bounded queue when a slot is busy; temporary slot
  occupancy is not misreported as resource exhaustion.
- Worker adapters execute in terminable child processes. Cancellation closes an
  in-flight upstream connection rather than waiting for inference to finish.
  Shutdown cancels, terminates and joins active children before returning.
- Canonical result schema includes result, evidence, warnings, review flag,
  complete provenance and five timing fields.
- Uploads are streamed into a bounded volatile memory store, never written to
  disk, never echoed, and cleared at shutdown.
- Metadata-only Prometheus metrics use bounded labels. Uvicorn access logging is
  disabled by the launcher example.

## Contract truth

`contracts/openapi.yaml` version `0.2.0-dev` marks each G-05 operation
`implemented-g05`. Future model/evaluation/responses/embedding/rerank/audio
operations remain in the same contract but are explicitly marked `planned`.
A test proves equality between exposed application routes and operations marked
implemented. Errors use the stable catalogue names and include a request ID.

## Automated evidence

Command: `pytest`

Result: **42 passed**.

Covered behaviours:

- public health/readiness and authenticated control-plane boundary;
- route-derived capability discovery without engine/model leakage;
- native job submit/status/result and canonical result-schema validation;
- same-key idempotent replay and conflicting-payload refusal;
- own-job isolation;
- running-job cancellation under 400 ms in the deterministic test;
- refusal before the configured memory floor;
- hard queue bound;
- concurrent one-heavy plus two-light execution;
- second heavy job waits rather than being rejected;
- restart convergence of incomplete jobs to explicit `WORKER_CRASHED`;
- bounded volatile upload and payload cleanup;
- SQLite mode `0600`, parent mode `0700` and metadata-only schema;
- payload-purging migration from schema v1 to v2 followed by a valid new insert;
- canonical `policy` requirement and strict OpenAI alias/field rejection;
- full canonical request-policy/version compatibility at schema boundaries;
- duplicate principal-name and duplicate token-value refusal;
- pre-validation native request byte ceiling and coordinator byte ceiling;
- one-megabyte child result drained without pipe deadlock;
- upstream response, single result and aggregate result-store byte ceilings;
- volatile result retention bounded by count and bytes with oldest-entry eviction;
- cancellation wins atomically against success, failure and timeout publication;
- shutdown terminates and joins active workers with no surviving child;
- synchronous OpenAI timeout maps to HTTP 504;
- native per-job timeout is enforced when stricter than the route timeout;
- validation errors do not echo input;
- OpenAI chat adapter through the same job core;
- secret token absent from responses;
- exact implemented-route/OpenAPI equality;
- fail-closed non-loopback configuration.

Additional deterministic gates:

- `ruff check runtime tests/test_runtime_g05.py`: **PASS**.
- `python -m compileall -q runtime tests`: **PASS**.
- `python scripts/validate_bootstrap.py`: required again at lot closure.

## Real-route smoke evidence

Surfaces were temporary and loopback-only:

- control plane: `127.0.0.1:8850`;
- llama-swap: `127.0.0.1:8840`;
- selected worker: llama.cpp `b10662`, route
  `text-extract-structured-balanced@2026-08`;
- model artefact: Qwen3-0.6B Q8_0, SHA-256
  `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.

Observed final smoke:

- health, readiness, system and metrics: HTTP 200 with request IDs;
- missing auth: HTTP 401, `AUTH_REQUIRED`, matching response request ID;
- structured job: HTTP 202, valid `Location`, terminal `succeeded`;
- synthetic input `Incident E42, gravité haute` returned schema-valid
  `{"code":"Incident E42","severity":"gravité haute"}`;
- canonical job-result schema validation: **PASS**;
- total structured-job time: **1,900 ms** including cold/on-demand path;
- SQLite parent/file modes `0700`/`0600`, no payload columns and no synthetic
  input bytes on disk;
- real running-job cancellation: terminal `cancelled` in **24 ms**;
- OpenAI chat adapter: HTTP 200, `chat.completion`, expected bounded answer.

After the smoke, both processes were stopped. Ports 8840 and 8850 were closed
and no job worker process remained.

## Explicit limits

- No permanent runtime service or package installation was created.
- No public or tailnet listener was created for the backend.
- No Hermes configuration was changed.
- No consumer production integration exists yet.
- The operations UI remains the accepted UI-00 simulated shell; it is not wired
  to live G-05 data.
- Native extraction and chat are proven; embeddings/rerank, vision/documents and
  audio remain G-06/G-07/G-08 work.
- Optional durable result retention and support-bundle policy require a later
  explicit gate; G-05 defaults to no payload persistence.
- Worker hard memory scope enforcement was proven in G-04 but is not yet
  packaged into a permanent supervisor.
