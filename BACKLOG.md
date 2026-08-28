# Backlog

Only the active slice is executable. Later slices are ordered hypotheses, not commitments.

## Closed — Takeover, UI-00, engine, G-05

G-00 through G-05 and UI-00 are closed on `main` (`2da6365`). Do not re-open
them without a new defect. Hub top-bar shortcut is in HermesHub `a7cd8dc`.

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
- [x] Hermes verifies the baseline and current branch.
- [x] Hermes produces the requirement-to-file coverage map.
- [x] Hermes refreshes the VM profile read-only and redacted.
- [x] Hermes updates state/handoff without installing anything.

## Next executable — G-06 (waiting for explicit GO)

- [ ] Vision and documents (`missions/04-vision-and-document-capabilities.md`).
- [ ] Do not start without Thomas's explicit lot decision.

## Next executable — UI-00

- [x] Read pinned UI canon and local contract.
- [x] Build Overview, Capabilities, Models, Jobs, Evaluations, Resources, Updates and Settings with simulated states.
- [x] Responsive desktop/mobile and keyboard verification.
- [x] Serve privately only after tests.
- [x] Stop for Thomas's explicit verdict — **verdict: ACCEPTÉ (2026-08-27, shell at `21cb372`)**.

## Post-acceptance — Engine spike

- [x] Measure VM headroom read-only (G-02).
- [x] Reproducible llama.cpp text/vision probes.
- [x] Evaluate llama-swap lifecycle.
- [x] Compare equivalent tasks in LocalAI; reject for profile A on measurement.
- [x] Test ONNX embeddings and native PDF discrimination; OCR and whisper remain
  explicitly gated to G-06/G-08.
- [x] Compare startup, idle/peak RAM, latency, cancellation, metrics, packaging, licence and recovery.
- [x] Prove G-04 hard cap, queue, 1-heavy + 2-light and crash recovery.
- [x] Amend ADRs and candidate registry.

## Gateway foundation

- [x] Health/readiness/discovery.
- [x] Jobs submit/status/cancel/result with terminable worker processes.
- [x] Idempotency and budgets.
- [x] Registry/routes/admission/leases.
- [x] Metadata-only request IDs and metrics; no payload logging.
- [x] OpenAI chat/model adapter through the native job core.
- [ ] Typed consumer clients after contract stabilisation.

## Capability families

- [ ] Vision and Hermes auxiliary route.
- [ ] Native PDF, OCR, layout and structured extraction.
- [ ] Object detection and image similarity.
- [ ] Embeddings and reranking.
- [ ] whisper.cpp and alternative ASR.

## Operations and release

- [ ] Packaging, service, model-store CLI, upgrade/rollback, notices, backup.
- [ ] Live operations UI and Hermes installation.
- [ ] Two independent consumers.
- [ ] Public release gates.

## Parked

Shared vector DB, universal RAG, agents, public SaaS, automatic cloud routing, fine-tuning, TTS, image/video generation, large coding main model, GPU vendor choice and billing.
