# G-06 vision and document report — 2026-08-28

Hardware profile: `hermes-cpu-8vcpu-16gib` (live: 10 vCPU / ~19.5 GiB / no GPU /
no swap). Control plane loopback-only. llama-swap started for one vision probe
then torn down. No permanent service, no model promotion, no live UI wiring,
no Hermes config change.

## What ran

- Synthetic public fixtures from `benchmarks/synthetic/generate.py`.
- Native PDF via `pdftotext`, image-only detection, Tesseract `fra+eng`.
- Deterministic invoice field extraction with French amount parsing.
- Saturated-box object detector and average-hash near-duplicate compare.
- One Qwen3-VL-2B loopback probe through existing spike-g03 llama-swap
  (`b10662` / `v251`) on `127.0.0.1:8860`.
- Pytest: G-05 + G-06 + bootstrap.

## Not run

- PaddleOCR / PP-OCR (not installed; remains `candidate`).
- Private-mounted corpus (not mounted).
- V-03 fine UI review, V-06 charts, V-09 multi-image.
- ONNX general object detector / semantic image embeddings.
- Permanent llama-swap or control-plane service.
- Live UI-01.

## Task families

See `registry/task-families.yaml`. Summary:

| Family | Result |
| --- | --- |
| V-01 screenshot description | pass on synthetic (VLM, 10267 ms, exact E42 + disk full) |
| V-02 UI error diagnosis | pass on synthetic (same probe; answered the question) |
| V-03 fine UI review | review, not measured |
| V-04 native PDF + OCR | pass; Tesseract mean confidence 0.9374; image-only PDF flagged |
| V-05 field extraction | pass; `SYN-0042` and `123,45` -> `123.45` |
| V-06 chart | review, not measured |
| V-07 objects | pass on synthetic red/blue boxes only |
| V-08 similarity | pass near-duplicate (1.0 vs 0.64); not semantic |
| V-09 multi-image | unsupported / not measured |
| V-10 tiny detail | pass abstention |

## Resource / safety

- No public bind.
- Uploads resolved by `upl_*` ids only; consumer filesystem paths rejected.
- Cloud fallback stayed false.
- Spike VLM process terminated after the probe.

## Rollback

Remove G-06 workers/routes and `registry/task-families.yaml`. G-05 job core
remains. Spike artefacts stay outside Git.
