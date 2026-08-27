# ADR-0008 — Local-first vision with specialists, VLM and explicit fallback

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-06

Small CPU VLM reduces cost/preserves privacy but does not universally match frontier reasoning. OCR, detection and similarity often need specialists. Route deterministic/native, specialists, general local VLM, then abstention/human/explicit remote fallback.

Hermes auxiliary vision must answer actual question, not generic caption, because text-only main model does not see pixels. Cloud disabled by default. Each task family is benchmarked separately.
