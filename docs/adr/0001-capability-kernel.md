# ADR-0001 — Capability kernel, not a model manager

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-00, G-05, G-10

## Context

Many applications and a future Hermes main local model need shared AI. A model catalogue would spread engine/quantisation/prompt/resource knowledge into consumers; a full platform would duplicate Hermes.

## Decision

Build a capability kernel owning contracts, routing, jobs, resource admission, model lifecycle, provenance, evaluation and compatibility adapters. Existing engines infer. Consumers own business data and decisions.

## Consequences

Consumers remain stable across model replacement; a native domain API is required; project must resist unrelated platform features.

## Validation

Two independent consumers use the same capability without shared domain logic/model config. If only one consumer exists after useful-tool phase, reassess lifetime value.
