# Vision evaluation

## Question

Which visual tasks can a small local CPU route replace, and which still require a stronger local model, human review, or explicitly authorised remote model?

## Task families

### V-01 — Screenshot description

Identify application type, major regions, visible state, and primary action.

### V-02 — UI error diagnosis

Answer a concrete question about a visible error, disabled control, overflow, modal, or layout defect. Generic captions score poorly.

### V-03 — Fine UI review

Evaluate hierarchy, spacing, consistency, responsiveness, state honesty, and accessibility signals. This is expected to expose the gap with frontier systems.

### V-04 — Document OCR

Exact French text, amounts, dates, IDs, accents, and line order.

### V-05 — Document field extraction

Return schema-validated fields with evidence and deterministic consistency checks.

### V-06 — Chart and diagram

Read legends, axes, relationships, and answer a question without inventing values.

### V-07 — Object detection

Return coordinates and labels. Compare specialist against VLM.

### V-08 — Image similarity

Near-duplicate, same object/product, and semantic similarity. Compare image embeddings against VLM judgement.

### V-09 — Multi-image reasoning

Compare two to four screenshots/pages and identify changes or relationships.

### V-10 — Tiny/ambiguous detail

Test abstention on unreadable text, crop, glare, compression, and uncertainty.

## Candidate routes

- Qwen3-VL 2B balanced;
- compact 1.5–1.6B candidate after licence review;
- SmolVLM2 500M fast triage;
- PP-OCRv6;
- PaddleOCR-VL/document pipeline;
- specialist object/image models to be selected;
- explicitly authorised frontier reference used only for comparison on public-safe inputs.

## Scoring

- exact task answer;
- factual precision/recall;
- OCR CER/WER;
- field exact match;
- schema pass;
- hallucination;
- correct abstention;
- evidence usefulness;
- cold/warm latency;
- peak memory;
- transformations;
- human review time saved.

## Replacement rule

A local route may be the default only for task families where it passes threshold. The UI and route registry show coverage by task family, not a single “vision supported” badge.
