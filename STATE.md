# State

Last updated: 2026-08-28 12:12 CEST (G-06 vision/document lot)

## Phase

Phases 0-4 complete through G-06 **by task family** on loopback. UI-00 remains
accepted simulated shell. No permanent runtime deployment. Not a daily-use
program yet.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- G-05 delivery: `952614e`; hardening: `2da6365`; Hub shortcut: HermesHub `a7cd8dc`.
- G-06 source: `runtime/` document and vision workers; evidence:
  `operations/G06-VISION-DOCUMENTS-2026-08-28.md` and
  `benchmarks/results/G06-VISION-DOCUMENTS-2026-08-28.md`.
- Task-family registry: `registry/task-families.yaml`.
- Permanent installation, Hermes config changes, live UI-01, production
  consumers: none. Spike artefacts and model weights remain outside Git.

## Current truth

Shared local AI capability kernel. UI-00 is still a labelled simulated console.
Local document native/OCR and bounded vision families are measured on synthetic
fixtures. They are not a universal vision stack.

## Gates

- G-00 to G-05 and UI-00: **passed** (unchanged).
- G-06 - Vision and documents: **passed by task family** (synthetic public
  fixtures; PaddleOCR and private corpus not measured).
- G-07 to G-11: **not started**.

## Next proof

G-07 (embedding and reranking) only after an explicit next-lot decision.
Mission: `missions/05-embeddings-and-reranking.md`.

## Blockers and risks

No blocker in the authorised G-06 lot. Permanent service, live UI wiring,
Hermes integration and consumer adoption remain unstarted.

Risks unchanged: false vision equivalence, resource interference,
consumer/model coupling, licence drift, public-data leakage, hidden cloud
fallback.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-06 authorised. G-06 closed by task family, not as universal vision.
- Hub top-bar shortcut requested and delivered.
