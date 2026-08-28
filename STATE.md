# State

Last updated: 2026-08-28 13:25 CEST (G-09 packaging lot)

## Phase

Phases 0-7 packaging slice complete through G-09 on a disposable prefix.
UI-00 remains accepted simulated shell. No permanent runtime deployment.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: pending G-09 commit.
- G-05 `952614e`; G-06 `faa6dac`; G-07 `fb4e059`; G-08 `3f496c9`.
- G-09 source: `installkit/`, `packaging/matrix.yaml`.
  Evidence: `operations/G09-PACKAGING-2026-08-28.md`.
- Permanent installation, Hermes config changes, live UI-01, production
  consumers: none. Spike artefacts and model weights remain outside Git.

## Current truth

Shared local AI capability kernel plus a rootless prefix installer. Loopback
is the only listen address. The systemd user unit is shipped and not enabled.

## Gates

- G-00 to G-08 and UI-00: **passed** (unchanged).
- G-09 - Packaging: **passed** as prefix install/uninstall (no permanent
  service, no model download, no Proxmox mutation).
- G-10 and G-11: **not started**.

## Next proof

G-10 (shared-runtime proof) only after an explicit next-lot decision.
Mission: `missions/08-hardening-packaging-release.md` (consumers only).

## Blockers and risks

No blocker in the authorised G-09 lot. Enabling the user unit, live UI,
Hermes integration and two consumers remain unstarted.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-09 authorised. G-09 closed as prefix packaging, not as a
  permanent service.
- Hub top-bar shortcut requested and delivered.
