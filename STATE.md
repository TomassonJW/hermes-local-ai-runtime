# State

Last updated: 2026-08-28 13:40 CEST (G-10 consumer lot)

## Phase

Phases 0-7 consumer proof complete through G-10 on loopback. UI-00 remains
accepted simulated shell. No permanent runtime deployment.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: pending G-10 commit.
- G-05 `952614e`; G-06 `faa6dac`; G-07 `fb4e059`; G-08 `3f496c9`; G-09 `f100d3b`.
- G-10 source: `consumers/`. Evidence: `operations/G10-CONSUMERS-2026-08-28.md`.
- Permanent installation, Hermes config changes, live UI-01: none.

## Current truth

Two in-repo consumers call capabilities, not model files. Sillage is an
example and does not define the product. Engine identity can change without
editing consumer code.

## Gates

- G-00 to G-09 and UI-00: **passed** (unchanged).
- G-10 - Shared-runtime proof: **passed** as synthetic Hermes + Sillage
  adapters (no live Hermes install, no production Sillage).
- G-11: **not started**.

## Next proof

G-11 (public release) only after an explicit next-lot decision.
Mission: `missions/08-hardening-packaging-release.md` (release slice).

## Blockers and risks

No blocker in the authorised G-10 lot. Live skill install, production
consumers and public release remain unstarted.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-10 authorised. G-10 closed as in-repo consumer proof.
- Hub top-bar shortcut requested and delivered.
