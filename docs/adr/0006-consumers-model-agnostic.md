# ADR-0006 — Consumers remain model-agnostic and own data

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-05, G-10

Consumers call capability/profile aliases, send bounded inputs/candidates, own validation/persistence/vector indexes/business actions and receive provenance/review state. Runtime holds no consumer DB credential, creates no business record, shares no universal vector store and exposes no raw model flags to ordinary consumers.

Validation: replace an approved model/engine without consumer code change.
