# ADR-0003 — Adapter boundary and LocalAI comparison (closed)

- Status: **Accepted — comparison performed, LocalAI rejected for profile A**
- Date: 2026-08-27, amended 2026-08-28
- Related gates: G-03
- Evidence: `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`

The mandatory comparison ran on the target VM. LocalAI v3.0.0 (`latest-cpu`, 3.88 GB image) exposed a compatible API and auto-discovered the GGUF models, but its llama-cpp backend never completed loading a 0.6B Q8 model within a 10-minute budget across two container attempts — on the same VM where pinned llama.cpp binaries serve the identical file in under 4 seconds cold. Combined with its 100× artefact weight and unwanted scope (image generation, TTS, galleries), LocalAI is rejected as execution substrate for deployment profile A.

The engine-neutral adapter boundary stands: the domain model never leaks engine concepts, so this decision remains reversible if a future gate re-opens the comparison with a materially different LocalAI. Ollama was not tested: llama-swap already provides the lifecycle layer with a thinner, pinned surface; revisit only if that layer fails.
