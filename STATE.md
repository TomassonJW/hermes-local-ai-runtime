# State

Last updated: 2026-08-28 12:48 CEST (G-07 embeddings/rerank lot)

## Phase

Phases 0-5 complete through G-07 on loopback. UI-00 remains accepted simulated
shell. No permanent runtime deployment. Not a daily-use program yet.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: `fb4e059`.
- G-05 delivery: `952614e`; G-06 delivery: `faa6dac`; Hub shortcut: HermesHub `a7cd8dc`.
- G-07 source: `runtime/vectors.py`, embed/rerank workers, `/v1/embeddings` and
  `/v1/rerank`. Evidence: `operations/G07-EMBEDDINGS-RERANK-2026-08-28.md`.
- Permanent installation, Hermes config changes, live UI-01, production
  consumers: none. Spike artefacts and model weights remain outside Git.

## Current truth

Shared local AI capability kernel. Embeddings are a computation: 1024-d L2
vectors with an opaque `space_id`. Rerank is bounded to 100 candidates. The
runtime does not host a vector database.

## Gates

- G-00 to G-06 and UI-00: **passed** (unchanged).
- G-07 - Embeddings and reranking: **passed** on synthetic multilingual
  fixtures (FastEmbed not wired; no private corpus; no shared vector DB).
- G-08 to G-11: **not started**.

## Next proof

G-08 (audio) only after an explicit next-lot decision.
Mission: `missions/06-audio.md`.

## Blockers and risks

No blocker in the authorised G-07 lot. Permanent service, live UI wiring,
Hermes integration and consumer adoption remain unstarted.

Risks unchanged: consumer/model coupling, mixing embedding spaces, resource
interference, public-data leakage, hidden cloud fallback.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-07 authorised. G-06 closed by task family. G-07 closed as
  computation, not as a vector database.
- Hub top-bar shortcut requested and delivered.
