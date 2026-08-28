# Local UI contract

## Authority

- Product: Hermes Local AI Runtime `0.1.0`
- UI canon repository: `TomassonJW/canonical-ui-design`
- UI canon version: `1.3.0`
- UI canon commit: `4d720bf20f3c89e9a9d71072f0b76d55d225cb62`
- Required procedure: `canonical-ui-design`
- First visible gate: UI-00 (closed)
- UI-01: live loopback console, waiting for visible verdict

## Interface purpose

The UI is an operations, evaluation, and model-governance console. It helps a technically capable operator understand the runtime without forcing low-level inference tuning during normal use.

It is not:

- a generic chat interface;
- an AI playground as the primary product;
- a consumer application's business UI;
- a raw wrapper around llama.cpp flags;
- a dashboard that shows fake live metrics.

## Users

### Operator

Installs, evaluates, promotes, deprecates, routes, observes, and rolls back.

### Developer/integrator

Finds capabilities, contracts, aliases, limits, examples, and job details.

### Product reviewer

Understands what the system can do, what is unavailable, what is risky, and what would happen before approving a change.

## Navigation

Persistent destinations:

1. **Essayer** (primary try surface)
2. **Overview**
3. **Capabilities**
4. **Models**
5. **Jobs**
6. **Evaluations**
7. **Resources**
8. **Updates**
9. **Settings**

A separate deep-linkable detail surface may show a capability, model, route, job, evaluation, worker, or event.

## Page contracts

### Overview

Answers:

- Is the runtime ready?
- What can it do now?
- What is loaded/running/waiting?
- Is the server under pressure?
- Are updates or blocked issues waiting?
- What is the next operator action?

Representative surfaces:

- readiness with reasons;
- capability-family coverage;
- active workers/models;
- queue summary;
- CPU/RAM pressure;
- latest evaluation/promotions;
- warnings and degradations.

### Capabilities

Displays stable capability contracts, not only model endpoints.

For each capability:

- availability;
- profiles;
- active route;
- limits;
- sync/async behaviour;
- data-class policy;
- task-family quality coverage;
- example request/response;
- consumers using it;
- fallback disabled/enabled with explicit scope.

### Models

Separates:

- discovered;
- candidates;
- installed/compatible;
- benchmarked;
- approved;
- deprecated;
- blocked.

Model detail:

- licence;
- source/revision/hashes;
- artefacts and disk size;
- compatible engines;
- capabilities;
- presets;
- benchmarks;
- loaded state and leases;
- update candidate;
- promotion/deprecation controls with consequences.

“Newest” is never equivalent to “recommended”.

### Jobs

Dense, filterable list with:

- job ID;
- consumer;
- capability/profile;
- state;
- queued/load/run duration;
- route;
- resource class;
- warning/review state;
- cancellation where valid.

Payload content is hidden by default. Details show metadata, evidence type, provenance, errors, and resource events.

### Evaluations

- suites and corpora;
- public/private/holdout status;
- run configuration;
- comparison;
- quality/resource regressions;
- promotion recommendation;
- downloadable public-safe report.

### Resources

- hardware profile;
- budget versus current;
- CPU/RAM/swap/queue;
- workers and leases;
- model residency/TTL;
- disk/model-store quota;
- admission and unload history;
- normal/burst/exclusive modes.

Metrics must distinguish “available”, “allocated”, “reserved”, “used”, and “estimated”.

### Updates

- engine/model candidate updates;
- licence or compatibility changes;
- changelog/release notes;
- disk impact;
- evaluation requirement;
- no automatic promotion.

### Settings

Sections:

- Interface;
- API and consumers;
- Routes and defaults;
- Resource budgets;
- Model store;
- Privacy and retention;
- Fallback;
- Observability;
- Backup and rollback;
- About and versions.

Setup is reachable through the canonical gear and deep link. Dangerous changes show impact and rollback.

## Global shell

Desktop:

- persistent topbar;
- resizable or responsive sidebar according to canon;
- main content;
- optional contextual detail panel only where useful;
- no mandatory IDE-like tabs or split view unless later usage proves value.

Mobile:

- compact navigation;
- primary status/action remains visible;
- dense tables transform into prioritised list/detail;
- no horizontal overflow required for core actions;
- confirmation consequences remain readable.

## State honesty

Every page defines:

- loading;
- empty;
- unavailable;
- blocked by gate;
- degraded;
- stale data;
- permission denied;
- partial failure;
- offline worker;
- no route approved.

Simulated UI-00 data is visibly labelled `Demo state — no runtime connected`.

## Language

Normal UI uses plain operational language:

- “Not enough memory to start this model” rather than “admission predicate false”;
- “Requires review” rather than a decorative confidence percentage;
- “Candidate, not used by applications” rather than “installed latest”.

Technical detail remains available progressively.

## Visual direction

- calm, dense, operational;
- strong hierarchy and legible data;
- no neon “AI” aesthetic;
- restrained motion;
- status uses text and icon, not colour alone;
- compact and data-grid densities available where canonical;
- system truth takes precedence over decoration.

## UI-00 representative data

Use a coherent simulated installation:

- CPU profile: 8 vCPU / 16 GiB / no GPU;
- one approved vision route candidate shown as simulated;
- OCR and embeddings available as simulated;
- one VLM unloaded;
- one OCR worker ready;
- three jobs: succeeded, queued, resource-rejected;
- one model update detected but not promoted;
- one licence-blocked candidate;
- resource pressure normal;
- cloud fallback disabled.

No simulated state may be labelled live.
