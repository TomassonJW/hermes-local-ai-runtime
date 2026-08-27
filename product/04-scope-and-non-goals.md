# Scope and non-goals

## In scope

Local capability gateway; jobs and bounded queues; resource admission/leases; model/engine registry; exact provenance; lifecycle/status; presets/routes; result cache; OpenAI adapter; optional MCP; OCR/document understanding; general vision; object/image specialists; embeddings/reranking; speech-to-text; operations/evaluation UI; CPU profile; future GPU/remote workers; packaging/observability/rollback/licence inventory.

## First-implementation non-goals

Generic chat, second Hermes agent framework, autonomous agents, universal RAG, shared vector DB, consumer DB access, business workflows, model marketplace, auto-promotion, silent cloud routing, fine-tuning, public SaaS, billing, image/video generation, TTS, GPU vendor selection, universal frontier vision parity, every model format/engine.

## Application boundary

Consumers own domain entities, authorisation, validation, persistence, confirmations, vector stores, business actions and retention. Runtime owns shared AI execution/metadata only.

## Hermes boundary

Hermes may use auxiliary vision, custom OpenAI-compatible main model, MCP/tools and future local inference. Runtime does not alter Hermes memory, sessions, skills, model config or gateway without an integration mission.

## Hypervisor boundary

Initial implementation lives inside existing Hermes VM. Bootstrap neither authorises nor requires Proxmox changes. Dedicated VM/LXC/GPU placement is a later infrastructure amendment.
