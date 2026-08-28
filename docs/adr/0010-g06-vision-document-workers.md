# ADR-0010 — G-06 vision and document workers on the G-05 job core

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-06
- Evidence: `operations/G06-VISION-DOCUMENTS-2026-08-28.md`

## Context

G-05 delivered a loopback capability/job core. G-06 must serve vision and
document task families without a permanent service, live UI wiring, Hermes
config mutation, or a single "vision supported" badge.

## Options considered

1. New standalone vision daemon - duplicates admission, auth and provenance.
2. Extend G-05 workers and routes - reuses the job boundary; reversible.
3. Call engines from the control plane in-process - couples crashes and deps.

## Decision

Reuse the G-05 job core. Add isolated worker kinds:

- `document-native` (Poppler `pdftotext`)
- `document-ocr` / `document-parse` / `document-structured` (Tesseract 5)
- `image-embed` / `object-detect` (deterministic CPU specialists)
- existing `openai-upstream` for local VLM images (llama.cpp via llama-swap)

Media crosses the process boundary only as upload ids resolved to job-scoped
temp files. Consumer filesystem paths and remote image URLs are rejected.
OpenAI-compatible vision aliases (`hlair/vision-balanced`) map to
`vision.analyze` and must answer the question, not caption. Cloud fallback
stays off. Task families are recorded individually; a family is `approved`
only after a measured synthetic pass.

PaddleOCR/PP-OCR remains a candidate until a disposable comparison actually
runs. Object detection and image similarity specialists in this lot are
bounded to synthetic geometry and perceptual hashes, not general scenes.

## Consequences

Positive: one admission/provenance path; honest per-family status; no new
listener family.

Negative: Tesseract is the measured OCR route, not PP-OCR; VLM quality is
CPU-2B and will fail fine UI review; specialists do not replace a detector
trained on natural images.

## Validation

Falsify a family if synthetic expected fields are missed, schema validation
is skipped, abstention fails on unreadable input, a remote URL is fetched,
or peak RSS crosses the G-04 heavy budget during the VLM probe.

## Rollback or amendment

Remove the new worker kinds and G-06 routes; G-05 echo/openai text routes
stay. Do not delete later unrelated work.
