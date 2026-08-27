# Mission 01 — UI-00 operations shell

## Goal

Deliver the complete visual shell and representative simulated states so Thomas can validate the product surface before runtime implementation.

## Required inputs

- pinned `canonical-ui-design` v1.3.0 commit;
- `ui/LOCAL-UI-CONTRACT.md`;
- `ui/UI-00-ACCEPTANCE.md`;
- product capability map;
- resource and model lifecycle chapters.

## Implementation freedom

Hermes chooses the frontend stack after checking compatibility with the environment and future backend. The shell must not create backend obligations that conflict with the engine spike.

## Required pages

- Overview;
- Capabilities;
- Models;
- Jobs;
- Evaluations;
- Resources;
- Updates;
- Settings.

## Required representative flows

1. inspect why runtime is not connected;
2. inspect a simulated vision capability and route;
3. inspect an approved versus candidate versus blocked model;
4. inspect a resource-rejected job;
5. understand CPU/RAM headroom;
6. inspect an update without promoting it;
7. open settings and see fallback disabled;
8. view mobile navigation and job details.

## Data rule

All data comes from a versioned UI fixture and is labelled simulated. No local system probe is read by the browser in UI-00.

## Delivery

- tests;
- browser verification;
- private route only if authorised;
- screenshots may be stored only with synthetic data;
- commit, push, rollback;
- stop and ask only for Thomas's visible-product verdict.

## Stop

No real API, model, worker, package installation, or service beyond the minimum UI preview/deployment authorised for UI-00.
