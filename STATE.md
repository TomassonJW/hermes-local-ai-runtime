# State

Last updated: 2026-08-28 23:10 CEST (UI-01 live defects fixed)

## Phase

G-00 through G-11 and UI-00 remain closed. UI-01 is **delivered for human
look**, not accepted. Runtime is on loopback only. systemd is not enabled.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Live console: `127.0.0.1:8830` behind `/apps/local-ai-runtime/`.
- llama-swap: `127.0.0.1:8840`. systemd not enabled.
- Evidence: `operations/UI01-LIVE-CONSOLE-2026-08-28.md`, ADR-0016, and
  `operations/UI01-DEFECTS-2026-08-28.md` for the two live defects fixed.

## Current truth

Runtime can be used from the private Hub URL. Not production-supported.
Not a daily-driver guarantee. UI-01 waits for Thomas's visible verdict.

Two live defects were found and fixed after the first delivery: the volatile
upload store starved after 8 uploads and killed every media capability, and
the runtime could not restart once its launching shell was gone. Both are
covered by regression tests and were verified against the running
deployment (20/20 uploads, restart with an empty environment, 13/13
capability sweep, pytest 93 passed).

The runtime is still a session process. A host reboot still leaves the
console down until someone restarts it.

## Gates

- G-00 to G-11 and UI-00: **passed**.
- UI-01: **delivered for look**, not accepted.

## Next proof

Thomas looks at the official URL and says if the cockpit is usable.