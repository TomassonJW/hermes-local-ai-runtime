# State

Last updated: 2026-08-28 10:04 CEST (handoff after G-05 + Hub shortcut)

## Phase

Phases 0-3 complete through G-05 on loopback. UI-00 accepted. Hub top-bar
shortcut added. No permanent runtime deployment. Not a daily-use program yet.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: `2da63655a6c5c845111f22e0d0524e6bc33bf492` = `origin/main`.
- Bootstrap validator and 46 tests pass (pinned deps, disposable venv outside the repo).
- Coverage map: `operations/COVERAGE-MAP-2026-08-27.md`.
- Live VM profile: `operations/LIVE-PROFILE-2026-08-27.md` - measured 10 vCPU /
  ~19.5 GiB / no GPU / no swap; conservative 8/16 budget kept.
- G-02/G-03/G-04 evidence: `operations/G02-ENVIRONMENT-PROBE-2026-08-27.md`
  and `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`.
- G-05 source and evidence: `runtime/` and
  `operations/G05-API-JOB-CORE-2026-08-28.md`.
- G-05 delivery: `952614e`; hardening: `2da6365`; CI `validate-bootstrap`
  run `33131398550` passed.
- HermesHub shortcut (not a grid card): commit `a7cd8dc`, slug
  `/apps/local-ai-runtime/`.
- Permanent installation, Hermes config changes, live UI-01, production
  consumers: none. Spike artefacts and model weights remain outside Git.

## Current truth

Shared local AI capability kernel for Hermes and other applications. Not a
Sillage feature and not a monolithic model server. First target: Hermes VM,
CPU-first, no GPU. UI-00 remains a labelled simulated console.

## Gates

- G-00 - Bootstrap integrity: **passed**.
- G-01 - Hermes takeover: **passed**.
- UI-00 - Operations shell: **ACCEPTED** (2026-08-27, commit `21cb372`).
- G-02 - Read-only environment probe: **passed**.
- G-03 - Engine spike: **passed**; llama.cpp `b10662` + llama-swap `v251`.
- G-04 - Resource safety: **passed** on the disposable spike.
- G-05 - API and job core: **passed on loopback**.
- G-06 to G-11: **not started**.

## Next proof

G-06 (vision and documents) only after an explicit next-lot decision.
Mission: `missions/04-vision-and-document-capabilities.md`. Reuse the G-05
job boundary. Do not claim universal vision quality.

## Blockers and risks

No blocker in the authorised G-02 through G-05 lot. Permanent service, live
UI wiring, Hermes integration and consumer adoption remain unstarted.

Risks: platform sprawl, false vision equivalence, resource interference,
consumer/model coupling, licence drift, public-data leakage, hidden cloud
fallback, premature GPU-specific architecture.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- General shared runtime; Sillage integrates later as one consumer.
- Useful operations UI desired.
- Open-source licence authorised.
- UI-00 accepted.
- G-02 through G-05 authorised and closed.
- Hub top-bar shortcut requested and delivered (like Dashboard / forfaits).
