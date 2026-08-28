# Handoff

Last updated: 2026-08-28 13:10 CEST

## Why this file exists

A new session must resume from Git. Notion is not required.

## Repository

- Public GitHub: `TomassonJW/hermes-local-ai-runtime`
- Canonical clone: this productions tree on the Hermes VM
- Official branch: `main`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` (`baseline/v0.1.0`)
- Verify `main` is clean at the G-08 commit or newer before mutation.

## Current lot

G-00 through G-08 and UI-00 are **closed**. G-08 is batch whisper.cpp
transcription. Streaming and Qwen3-ASR are not implemented.

Do not reopen G-00 to G-08 without a new defect.

## Hard stops still in force

Do not install a permanent service, download/promote production weights, expose
beyond the authorised private boundary, write consumer data, wire live UI-01,
change Hermes `config.yaml`, or start G-09 until Thomas gives an explicit lot
decision.

## What already exists

- UI-00 simulated shell at `ui/shell/dist/`
- Hub top-bar IA locale -> `/apps/local-ai-runtime/` (HermesHub `a7cd8dc`)
- G-05 job core on loopback
- G-06 vision/document workers
- G-07 embed/rerank workers
- G-08 whisper.cpp audio worker
- Spike-g03 binaries and weights **outside Git**

## Next lot

G-09. Mission: `missions/08-hardening-packaging-release.md`.
Do not start a permanent service in that lot without an explicit install decision.

## Resume checklist

1. Read `AGENTS.md`, `STATE.md`, this file, `GATES.md`.
2. Confirm `main` is clean.
3. Do not start G-09 without explicit GO.
4. If the Hub button is dead, restart only the UI-00 static server.

## Evidence

- G-03: `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`
- G-05: `operations/G05-API-JOB-CORE-2026-08-28.md`
- G-06: `operations/G06-VISION-DOCUMENTS-2026-08-28.md`
- G-07: `operations/G07-EMBEDDINGS-RERANK-2026-08-28.md`
- G-08: `operations/G08-AUDIO-2026-08-28.md`
