# State

Last updated: 2026-08-28 14:00 CEST (G-11 public source lot)

## Phase

G-00 through G-11 and UI-00 closed on loopback/source terms. UI-00 remains
the accepted simulated shell. No permanent runtime deployment.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: pending G-11 commit.
- G-11 source: `RELEASE.md`, `packaging/checksums.sha256`, `docs/security-review-g11.md`.
  Evidence: `operations/G11-PUBLIC-RELEASE-2026-08-28.md`.
- Permanent installation, Hermes config changes, live UI-01: none.

## Current truth

Public source candidate. Loopback job core and prefix installer exist. Not a
daily-use program. Not production-supported. Not a substitute for large cloud
models.

## Gates

- G-00 to G-10 and UI-00: **passed** (unchanged).
- G-11 - Public release: **passed** as source candidate (no production tag,
  no systemd enable, no cloud-model substitute claim).

## Next proof

No further gated lot. Later work needs a new explicit decision (live UI,
permanent service, Hermes skill install, or production consumers).

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-11 authorised. G-11 closed as source publication, not as
  production support.
- Hub top-bar shortcut requested and delivered.
