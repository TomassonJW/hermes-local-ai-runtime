# Backlog

Only the active slice is executable. Later slices are ordered hypotheses, not commitments.

## Closed — Takeover, UI-00, engine, G-05, G-06, G-07

G-00 through G-07 and UI-00 are closed on `main`. Do not re-open them without a
new defect. Hub top-bar shortcut is in HermesHub `a7cd8dc`.

- [x] Shared capability-kernel boundary.
- [x] Actual VM profile separated from host capacity.
- [x] Resource/privacy/licence/model lifecycle/fallback invariants.
- [x] UI-00 and absolute stop.
- [x] Native and compatibility API candidates.
- [x] Capability/model candidate registry.
- [x] Hermes integration and thin skill contract.
- [x] Missions and gates.
- [x] CI validates the baseline.
- [x] Final SHA recorded in `BASELINE.md`.
- [x] G-02 through G-05 on loopback.
- [x] G-06 vision/document families on synthetic fixtures.
- [x] G-07 embeddings and bounded rerank (no shared vector DB).

## Next executable — G-08 (waiting for explicit GO)

- [ ] Audio transcription (`missions/06-audio.md`).
- [ ] Do not start without Thomas's explicit lot decision.

## Capability families

- [x] Vision and Hermes auxiliary route (synthetic V-01/V-02; V-03/V-06/V-09 still review).
- [x] Native PDF, Tesseract OCR and deterministic structured extraction (PaddleOCR not measured).
- [x] Synthetic object detection and near-duplicate hash (not general ONNX / semantic embed).
- [x] Embeddings and reranking (1024-d L2; FastEmbed not wired).
- [ ] whisper.cpp and alternative ASR.

## Operations and release

- [ ] Packaging, service, model-store CLI, upgrade/rollback, notices, backup.
- [ ] Live operations UI and Hermes installation.
- [ ] Two independent consumers.
- [ ] Public release gates.

## Parked

Shared vector DB, universal RAG, agents, public SaaS, automatic cloud routing, fine-tuning, TTS, image/video generation, large coding main model, GPU vendor choice and billing.
