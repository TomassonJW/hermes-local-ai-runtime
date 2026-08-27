# Operations and observability

## Daily operator view

- readiness;
- warnings;
- queue and oldest job;
- active model/worker leases;
- resource pressure;
- failed/review-required jobs by count;
- disk/model-store usage;
- candidate updates;
- last successful backup/checkpoint.

## Alerts candidate

### Critical

- OOM or hard memory breach;
- public listener detected unexpectedly;
- unauthorised cloud request;
- secret/payload logging detected;
- metadata state corruption;
- repeated worker crash loop;
- model hash mismatch.

### High

- sustained swap growth;
- queue full for interactive jobs;
- readiness unavailable;
- other Hermes service latency breach during accepted load;
- disk quota near full;
- licence status becomes blocked.

### Warning

- model fails to unload after TTL;
- candidate update available;
- evaluation regression;
- backup/checkpoint stale;
- high review-required rate;
- cache or temp cleanup backlog.

## Health semantics

`/healthz` means the control-plane process can answer.

`/readyz` means configuration/state are valid and at least one advertised route can accept according to policy. It may be false while the process is healthy.

A specific capability may be unavailable while global readiness remains true. Capability discovery is authoritative.

## Operator actions

- drain runtime;
- pause admission by priority;
- cancel job;
- unload idle model;
- quarantine worker/model;
- run evaluation;
- promote/deprecate route;
- export public-safe support bundle;
- create checkpoint;
- initiate rollback.

Every action records actor, reason, impact, and resulting revision without payload content.
