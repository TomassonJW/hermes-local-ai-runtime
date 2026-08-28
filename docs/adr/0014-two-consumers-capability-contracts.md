# ADR-0014 - Two consumers on capability contracts, not model names

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-10

## Context

G-10 requires two independent consumers on stable capability contracts.
Sillage may be one example. It must not define the product.

## Options considered

1. Install the thin Hermes skill globally and mutate Hermes config.
2. Keep both consumers in-repo, HTTP-only, no live Hermes mutation.

## Decision

Option 2 for this lot. `consumers/hermes_app.py` and `consumers/sillage_app.py`
call `/api/v1/capabilities` then `/api/v1/jobs`. They do not name engines or
checkpoint files. Replacing `engine_version` does not change consumer code.
Sillage persists invoices in its own SQLite file. The runtime never receives
that path or a credential.

## Consequences

The proof is synthetic and loopback. Live Hermes skill installation and a
production Sillage adapter remain later work.

## Validation

`tests/test_runtime_g10.py` and `scripts/g10_eval.py`.

## Rollback or amendment

Remove `consumers/` and the G-10 tests. No systemd unit, no Hermes config,
no consumer database was written outside the test prefix.
