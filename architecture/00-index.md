# Architecture index

Read in order:

1. [`01-system-context.md`](01-system-context.md)
2. [`02-control-plane-and-workers.md`](02-control-plane-and-workers.md)
3. [`03-resource-governance.md`](03-resource-governance.md)
4. [`04-security-and-data-boundaries.md`](04-security-and-data-boundaries.md)
5. [`05-deployment-profiles.md`](05-deployment-profiles.md)
6. [`06-model-lifecycle.md`](06-model-lifecycle.md)
7. [`07-hermes-integration.md`](07-hermes-integration.md)
8. [`08-api-and-job-model.md`](08-api-and-job-model.md)
9. [`09-future-gpu-and-distributed-workers.md`](09-future-gpu-and-distributed-workers.md)
10. [`10-observability-and-provenance.md`](10-observability-and-provenance.md)

## Style

Modular monolith control plane initially; isolated worker processes by runtime family; capability-first domain; engine adapters; asynchronous job core with bounded synchronous convenience; local model artefact store; small durable metadata store selected during implementation; no distributed system until a second execution node exists; no shared business-data store.

Product boundaries are accepted. Framework, database, container, supervisor and packaging choices remain spike/ADR decisions.
