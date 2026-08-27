# Handoff

Date: 2026-08-27  
Project: Hermes Local AI Runtime  
Repository: `TomassonJW/hermes-local-ai-runtime`  
Version: `0.1.0`

## Handoff status

Product and engineering constitution compiled. Runtime not implemented. The baseline commit is recorded in `BASELINE.md` after compilation.

## Mandatory takeover prompt

```text
Take over TomassonJW/hermes-local-ai-runtime from the baseline recorded in BASELINE.md.

Clone it or update the existing clone without overwriting foreign work. Read AGENTS.md, provenance/COMPILATION-MANIFEST.yml, product/00-index.md, architecture/00-index.md, GATES.md, STATE.md, HANDOFF.md, and the complete active constitution in the prescribed order. Run the bootstrap validator and produce a coverage map.

You own operational Git, local architecture, roadmap, backlog, ADRs, implementation, tests, deployment, and future handoffs. Do not return to Notion during ordinary sessions.

The repository authorises only safe takeover and read-only preflight. Because the product includes an interface, execute UI-00 first using the pinned canonical UI baseline and ui/LOCAL-UI-CONTRACT.md. Build a truthful operations shell with simulated data only, serve and verify it on the authorised private surface, then stop before UI-01 and before any runtime backend, permanent package, service, model download, or Hermes configuration change. Wait for Thomas's explicit visible-product verdict.
```

## First session

Verify baseline/Git; run validator/tests; read the corpus; produce a coverage map; refresh VM profile read-only and redacted; prepare and implement only UI-00; update state/handoff; stop for Thomas.

## Do not do

Do not install inference engines permanently, download weights, expose beyond the authorised private boundary, modify Proxmox/unrelated services, add Sillage domain logic, claim universal vision replacement, start backend before UI-00 acceptance, choose NVIDIA/AMD, or create generic chat.

## Key decisions

Capability-first API; OpenAI facade; optional MCP; llama.cpp first candidate not lock-in; LocalAI comparison; specialist OCR/vector/audio; one heavy CPU inference; local-first fallback disabled by default; consumers own data and writes.

## Next hard stop

Thomas's explicit acceptance or rejection of UI-00.
