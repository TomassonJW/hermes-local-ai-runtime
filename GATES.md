# Gates

A gate is a hard permission boundary, not a progress label. A later gate cannot compensate for an earlier failed gate.

## G-00 — Bootstrap integrity

Pass when required files exist; JSON/YAML parse; links and pins validate; product, architecture, API, missions, state, and handoff agree; target hardware is explicit; no secret/private corpus is committed; and the repository is autonomous without Notion.

Evidence: `python scripts/validate_bootstrap.py`, `pytest`, anti-secret review, and baseline recorded in `BASELINE.md`.

## G-01 — Hermes takeover

Hermes safely clones/updates, reads the corpus, confirms Git state and baseline, creates no package/model/service/port, records unknowns, and updates state/handoff. Stop if the live VM materially contradicts 8 vCPU / 16 GiB / no GPU.

## UI-00 — Operations shell

Must provide truthful simulated Overview, Capabilities, Models, Jobs, Evaluations, Resources, Updates, Settings, and explicit empty/loading/degraded/blocked/failure states.

Must not provide real inference, a permanent backend, model downloads, fake live metrics, or generic chat as the primary surface.

Pass only after canonical UI checks, desktop/mobile verification, private URL verification when authorised, and Thomas's explicit verdict.

**Absolute stop (historical):** UI-00 required Thomas's verdict before UI-01.
UI-01 was authorised 2026-08-28. The live console is not accepted until the
visible verdict.

## G-02 — Read-only environment probe

Record public-safe OS, architecture, CPU features, allocated vCPU/RAM, disk, current headroom and prerequisites, distinguishing host capacity from VM allocation. No mutation.

## G-03 — Engine spike

Compare equivalent bounded tasks through llama.cpp plus lifecycle, LocalAI, Ollama only if useful, and direct specialist workers. Test structured text, image, embedding, rerank, load/idle/unload, cancellation, timeout, metrics, loopback, and recovery. Select the thinnest measured architecture.

## G-04 — Resource safety

On the actual VM prove hard memory limits, explicit refusal before pressure, responsive representative Hermes services, TTL/pressure unload, cancellation, crash recovery, one heavy job, two light jobs and bounded queue.

Initial candidate budget: 4 normal CPU cores, burst to 6, 8 GiB soft memory, 10 GiB hard memory, queue 8, no sustained swap growth.

## G-05 — API and job core

Native `/api/v1` discovery/jobs and compatibility adapters validate; idempotency, sync/async selection, auth, limits, provenance, warnings and cancellation are tested.

## G-06 — Vision and document vertical

Compare native text extraction, preprocessing, OCR, document layout/parser, general VLM and structured schema extraction. Return low-confidence/unsupported honestly. Hermes auxiliary vision must answer the actual question, not only caption.

## G-07 — Embedding and reranking vertical

Pinned deterministic vectors with dimensions/normalisation; bounded rerank candidates; no shared application vector DB; multilingual quality/resource benchmark; consumer persists vectors without model filename.

## G-08 — Audio vertical

Measure whisper.cpp CPU baseline, French quality, real-time factor, memory, VAD, cancellation and long-file chunking. Larger Whisper and alternative ASR remain resource-gated.

## G-09 — Packaging and safe installation

Fresh supported Linux install, pinned versions, no Proxmox mutation, loopback default, explicit paths/quotas, uninstall/rollback, notices and upgrade recovery.

## G-10 — Shared-runtime proof

At least two independent consumers use stable capability contracts. Sillage may be one but cannot define the product.

## G-11 — Public release

Requires support matrix, reproducible install/uninstall, API compatibility policy, public synthetic evaluation, security review, licence inventory, CI/release artefacts, and no universal frontier-parity claim.

## UI-01 — Live loopback console

Serve the operations console from the running control plane on loopback.
Operator try surface uses capabilities and profiles, not GGUF filenames.
Pass only after Thomas's visible verdict. systemd remains not enabled.
