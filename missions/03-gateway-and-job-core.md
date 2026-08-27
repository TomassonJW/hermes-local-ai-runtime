# Mission 03 — Capability gateway and job core

## Goal

Implement a minimal production-shaped vertical from capability request to admitted worker result.

## Scope

- `/healthz`, `/readyz`;
- `/api/v1/system`;
- `/api/v1/capabilities`;
- submit/status/cancel/result;
- authentication boundary;
- bounded upload;
- route registry;
- admission;
- one dummy worker, then one approved real route;
- provenance;
- metadata logs and metrics;
- OpenAI-compatible adapter for the selected real route.

## First vertical

Prefer `text.extract_structured` or a small embedding route because it can exercise:

- schema;
- route;
- admission;
- worker lifecycle;
- validation;
- cache;
- provenance;
- cancellation;
- compatibility.

Do not start with a complex multipage document pipeline.

## Quality

- typed internal models;
- migrations for durable metadata;
- idempotency;
- immutable results;
- explicit errors;
- no payload logs;
- integration tests;
- process restart tests;
- resource gate tests.

## Acceptance

G-05 passes on loopback. No consumer production integration yet.
