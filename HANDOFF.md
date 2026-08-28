# Handoff

Last updated: 2026-08-28 12:48 CEST

## Why this file exists

A new session must resume from Git. Notion is not required.

## Repository

- Public GitHub: `TomassonJW/hermes-local-ai-runtime`
- Canonical clone: this productions tree on the Hermes VM
- Official branch: `main`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` (`baseline/v0.1.0`)
- Verify `main` is clean at the G-07 commit or newer before mutation.

## Current lot

G-00 through G-07 and UI-00 are **closed**. G-07 is computation-only embeddings
and bounded rerank. No shared vector database.

Do not reopen G-00 to G-07 without a new defect.

## Hard stops still in force

Do not install a permanent service, download/promote production weights, expose
beyond the authorised private boundary, write consumer data, wire live UI-01,
change Hermes `config.yaml`, or start G-08 until Thomas gives an explicit lot
decision.

## What already exists

- UI-00 simulated shell at `ui/shell/dist/`, preview `python3 -m http.server 8830 --bind 127.0.0.1`
- Hub top-bar « IA locale » -> `/apps/local-ai-runtime/` (HermesHub `a7cd8dc`)
- G-05 job core on loopback
- G-06 vision/document workers
- G-07 embed/rerank workers and adapters
- Spike-g03 llama.cpp/llama-swap + weights **outside Git**

## Next lot

G-08. Mission: `missions/06-audio.md`. Reuse the G-05 job
boundary. Do not start a permanent ASR service.

## Resume checklist

1. Read `AGENTS.md`, `STATE.md`, this file, `GATES.md`.
2. Confirm `main` is clean.
3. Do not start G-08 without explicit GO.
4. If the Hub button is dead, restart only the UI-00 static server.

## Evidence

- G-03: `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`
- G-05: `operations/G05-API-JOB-CORE-2026-08-28.md`
- G-06: `operations/G06-VISION-DOCUMENTS-2026-08-28.md`
- G-07: `operations/G07-EMBEDDINGS-RERANK-2026-08-28.md`
