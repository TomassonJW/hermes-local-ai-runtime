# G-06 vision and document core — 2026-08-28

Lot authorised by explicit `GO G-06`. Reuses the G-05 job core. No permanent
runtime service, no live UI wiring, no Hermes `config.yaml` mutation, no
production model promotion.

## Delivered

- Document workers: native PDF, Tesseract OCR, parse, structured extract.
- Vision specialists: saturated-box detector, average-hash compare, tiny-image
  abstention.
- OpenAI-compatible alias `hlair/vision-balanced` (data-URL images only).
- Upload ids materialised to job-scoped temp files; paths from callers rejected.
- Synthetic fixture generator and G-06 tests.
- Task-family registry: `registry/task-families.yaml`.

## Evidence

- Tests: `pytest` (G-05 + G-06 + bootstrap).
- Evaluation: `python3 scripts/g06_eval.py --with-vlm`
- Report: `benchmarks/results/G06-VISION-DOCUMENTS-2026-08-28.md`
- ADR: `docs/adr/0010-g06-vision-document-workers.md`

## Limits

G-06 passes **by task family**, not as universal vision. PaddleOCR, private
corpus, fine UI review, charts, multi-image reasoning and a general ONNX
detector were not measured. UI-00 stays simulated.

## Rollback

Delete G-06 workers, routes, registry file and tests. Leave G-05 untouched.
