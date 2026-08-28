# Handoff

Last updated: 2026-08-28 16:10 CEST

## Why this file exists

A new session must resume from Git. Notion is not required.

## Repository

- Public GitHub: `TomassonJW/hermes-local-ai-runtime`
- Canonical clone: this productions tree on the Hermes VM
- Official branch: `main`
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` (`baseline/v0.1.0`)
- Verify `main` is clean before mutation.

## Current lot

UI-01 live loopback console. G-00 to G-11 and UI-00 stay closed.

## Hard stops still in force

Do not enable systemd, download/promote production weights, expose beyond
the private Tailscale path, write consumer data, or change Hermes
`config.yaml` without a new explicit decision.

## What already exists

- Live UI + API on `127.0.0.1:8830`
- llama-swap on `127.0.0.1:8840`
- Hub path `/apps/local-ai-runtime/`
- Hermes skill `hermes-local-ai-runtime` in the default profile
- Spike-g03 binaries and weights outside Git

## Next lot

Wait for Sillage (or another app) to load Hermes skill `hermes-local-ai-runtime`.
No gated lot here. UI-01 cockpit was used live.

## Resume checklist

1. Read `AGENTS.md`, `STATE.md`, this file, `GATES.md`.
2. Confirm `127.0.0.1:8830/healthz` is ok before claiming the console is down.
3. Restart with `HERMES_LOCAL_AI_SERVE_UI=1 python3 -m runtime --config state/ui01-runtime.yaml` plus llama-swap on 8840.

## Evidence

- UI-01: `operations/UI01-LIVE-CONSOLE-2026-08-28.md`