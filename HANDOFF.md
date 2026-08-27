# Handoff

- Date: 2026-08-27 (updated by Hermes after G-01)
- Project: Hermes Local AI Runtime
- Repository: `TomassonJW/hermes-local-ai-runtime`
- Version: `0.1.0`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21`
- Baseline branch: `baseline/v0.1.0`

## Handoff status

Hermes completed G-01 (safe clone, corpus read, validator + tests pass, coverage
map and redacted live profile committed) and delivered UI-00: a complete
operations shell (Overview, Capabilities, Models, Jobs, Evaluations, Resources,
Updates, Settings + deep-linkable details) built from a versioned simulated
fixture, tested (14 UI tests, typecheck, build), verified in a real headless
browser on desktop and mobile viewports against the official private tailnet
route, with zero console errors. Evidence and registry:
`ui/UI-00-PAGE-REGISTRY.md`. Serving: static build behind the private tailnet
path `/apps/local-ai-runtime` (loopback file server; restart command in
`ui/shell/README.md`). Live VM measures 10 vCPU / ~19.5 GiB / no GPU / no swap
device; conservative budgets unchanged; profile amendment proposed, not applied.

**Hard stop reached: awaiting Thomas's explicit UI-00 verdict.** Runtime
backend, UI-01, packages, services, model downloads and Hermes config changes
remain forbidden until that verdict and G-02.

## Mandatory takeover prompt

```text
Take over TomassonJW/hermes-local-ai-runtime from the baseline recorded in BASELINE.md.

Clone it or update the existing clone without overwriting foreign work. Read AGENTS.md, provenance/COMPILATION-MANIFEST.yml, product/00-index.md, architecture/00-index.md, GATES.md, STATE.md, HANDOFF.md, and the complete active constitution in the prescribed order. Run the bootstrap validator and produce a coverage map.

You own operational Git, local architecture, roadmap, backlog, ADRs, implementation, tests, deployment, and future handoffs. Do not return to Notion during ordinary sessions.

The repository authorises only safe takeover and read-only preflight. Because the product includes an interface, execute UI-00 first using the pinned canonical UI baseline and ui/LOCAL-UI-CONTRACT.md. Build a truthful operations shell with simulated data only, serve and verify it on the authorised private surface, then stop before UI-01 and before any runtime backend, permanent package, service, model download, or Hermes configuration change. Wait for Thomas's explicit visible-product verdict.
```

## First session

1. Verify baseline, branch, remote and working tree.
2. Run `python scripts/validate_bootstrap.py` and `pytest`.
3. Read the corpus and produce a coverage map.
4. Refresh VM allocation/headroom/prerequisites read-only and redact the report.
5. Update `STATE.md`, `HANDOFF.md` and active backlog.
6. Commit and push the read-only takeover evidence.
7. Prepare UI-00; do not install or start the AI runtime.

## Do not do

Do not install inference engines permanently, download weights, expose beyond the authorised private boundary, modify Proxmox/unrelated services, add Sillage domain logic, claim universal vision replacement, start backend before UI-00 acceptance, choose NVIDIA/AMD, or create generic chat.

## Key decisions

Capability-first API; OpenAI facade; optional MCP; llama.cpp first candidate not lock-in; LocalAI comparison; specialist OCR/vector/audio; one heavy CPU inference; local-first fallback disabled by default; consumers own data and writes.

## Next hard stop

Thomas's explicit acceptance or rejection of UI-00.
