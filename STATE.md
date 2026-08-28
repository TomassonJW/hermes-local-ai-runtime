# State

Last updated: 2026-08-28 15:30 CEST (UI-01 live console candidate)

## Phase

G-00 through G-11 and UI-00 remain closed. UI-01 is **delivered for human
look**, not accepted. Runtime is on loopback only. systemd is not enabled.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Current `main` was `242bd34` before this lot; UI-01 is a new commit.
- Live console: `127.0.0.1:8830` behind `/apps/local-ai-runtime/`.
- llama-swap: `127.0.0.1:8840`. systemd not enabled.
- Evidence: `operations/UI01-LIVE-CONSOLE-2026-08-28.md`. ADR-0016.

## Current truth

Runtime can be used from the private Hub URL. Not production-supported.
Not a daily-driver guarantee. UI-01 waits for Thomas's visible verdict.

## Gates

- G-00 to G-11 and UI-00: **passed**.
- UI-01: **delivered for look**, not accepted.

## Next proof

Thomas looks at the official URL and says if the cockpit is usable.