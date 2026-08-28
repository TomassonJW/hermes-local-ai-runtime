# ADR-0015 - Public source candidate, not production support

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-11

## Context

G-11 asks for a public release: matrix, install, API policy, synthetic
evaluation, security review, licence inventory, CI checksums. It does not
authorise a production service.

## Decision

Publish the tree as a source candidate. Do not enable systemd. Do not claim
production support. Do not claim equivalence with large cloud models.

## Validation

`tests/test_runtime_g11.py` and `python3 -m installkit checksums --verify`.
