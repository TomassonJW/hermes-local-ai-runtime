# State

Last updated: 2026-08-29 00:20 CEST (UI-01 accepted)

## Phase

G-00 through G-11, UI-00 and UI-01 are closed. Runtime is on loopback only,
supervised by systemd user services (ADR-0017).

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Live console: `127.0.0.1:8830` behind `/apps/local-ai-runtime/`.
- llama-swap: `127.0.0.1:8840`. Both processes run as systemd user services
  (`hlair.target`), enabled at boot with crash restart.
- Evidence: `operations/UI01-LIVE-CONSOLE-2026-08-28.md`, ADR-0016, ADR-0017,
  `operations/RUNBOOK-systemd.md`, and
  `operations/UI01-DEFECTS-2026-08-28.md` for the two live defects fixed.

## Current truth

Runtime is usable from the private Hub URL and UI-01 was accepted by Thomas on
2026-08-29 ("UI-01 pass"). Acceptance covers the cockpit as a private
operations console; it is not a production-support or daily-driver guarantee.

Two live defects were found and fixed after the first delivery: the volatile
upload store starved after 8 uploads and killed every media capability, and
the runtime could not restart once its launching shell was gone. Both are
covered by regression tests and were verified against the running
deployment (20/20 uploads, restart with an empty environment, 13/13
capability sweep, pytest 93 passed).

The runtime is no longer a session process. systemd user services were enabled
on 2026-08-28 at Thomas's explicit request: both the controller and the model
router start at boot (user lingering is on) and restart on failure. Verified by
killing the controller with SIGKILL (systemd restarted it, health back to 200)
and by a full stop/start of `hlair.target`, followed by a 13/13 capability
sweep under systemd.

## Gates

- G-00 to G-11, UI-00 and UI-01: **passed**.

## Next proof

No lot is open. The next one requires an explicit decision from Thomas.
A candidate is a second independent consumer loading the Hermes skill
`hermes-local-ai-runtime`, which would exercise the G-10 contract for real.