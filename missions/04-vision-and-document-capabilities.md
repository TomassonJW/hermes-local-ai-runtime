# Mission 04 — Vision and document capabilities

## Goal

Deliver a routed local-first stack that can serve Hermes auxiliary vision and application document tasks without pretending universal parity.

## Vertical slices

### Slice A — Hermes auxiliary vision

- OpenAI-compatible model alias;
- image + actual question;
- local VLM route;
- direct answer, evidence/warnings, review status;
- compatibility test with installed Hermes version.

### Slice B — Document native/OCR

- native PDF text first;
- image-only detection;
- preprocessing;
- PP-OCR/Tesseract comparison;
- regions/confidence.

### Slice C — Layout and structured extraction

- PaddleOCR/document parser;
- route specialist output into schema extraction;
- deterministic validation;
- low-confidence and unsupported outcomes.

### Slice D — Object/image specialists

- select ONNX detector and image embedding candidate by benchmark;
- coordinates/similarity;
- optional VLM semantic second pass.

## Evaluation

Run `benchmarks/VISION-EVALUATION.md` on:

- synthetic public fixtures;
- private-mounted corpus;
- holdout where available;
- actual CPU resource guardrails.

## Cloud reference

A frontier model may be used as an evaluation reference only with public-safe fixtures or explicit private-data authorisation. It is not the ground truth by itself.

## Acceptance

G-06 passes by task family. Registry and UI show which local tasks are approved and which require review/fallback.
