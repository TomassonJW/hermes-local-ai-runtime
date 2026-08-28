# State

Last updated: 2026-08-28 (G-05 closed)

## Phase

Phase 3 complete through G-05: measured engine/resource foundation and the API
job core are validated on loopback. No permanent runtime deployment exists.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0` — verified present in clone.
- Operational owner: Hermes (clone at the canonical productions workspace on the Hermes VM).
- Bootstrap validator and 46 tests pass on this clone (pinned deps, disposable venv outside the repo).
- Coverage map produced: `operations/COVERAGE-MAP-2026-08-27.md`.
- Live VM profile refreshed read-only: `operations/LIVE-PROFILE-2026-08-27.md` — measured 10 vCPU / ~19.5 GiB / no GPU / no swap device; favorable vs pinned 8/16, conservative budget kept; profile update proposed, not applied.
- G-02/G-03/G-04 evidence: `operations/G02-ENVIRONMENT-PROBE-2026-08-27.md`
  and `benchmarks/results/G03-ENGINE-SPIKE-2026-08-28.md`.
- G-05 control-plane source and evidence: `runtime/` and
  `operations/G05-API-JOB-CORE-2026-08-28.md`.
- G-05 implementation commit: `952614e`; GitHub Actions
  `validate-bootstrap` run `33130282636`: **passed**.
- Permanent installation/runtime service, Hermes configuration changes and
  production consumers: none. Spike artefacts and model weights remain outside Git.
- Current authority: this repository.

## Current truth

The product is a shared local AI capability kernel for Hermes and other applications. It is not a Sillage feature and not a monolithic model server. It assembles replaceable engines and adds capability contracts, routing, resource admission, model governance, provenance, evaluation, compatibility APIs and operations.

The first deployment target is the existing Hermes VM with 8 vCPU, 16 GiB RAM and no GPU. The Proxmox host has more total CPU/RAM, but those resources are not automatically available inside the VM. The live profile must still be refreshed read-only during G-01/G-02.

## Gates

- G-00 — Bootstrap integrity: **passed**.
- G-01 — Hermes takeover: **passed** (evidence in `operations/`).
- UI-00 — Operations shell: **ACCEPTED** — explicit verdict « ACCEPTÉ » from Thomas, 2026-08-27, on the shell at commit `21cb372` served on the private surface.
- G-02 — Read-only environment probe: **passed**.
- G-03 — Engine spike: **passed**; llama.cpp `b10662` + llama-swap `v251`
  selected, LocalAI rejected on measured profile-A behaviour.
- G-04 — Resource safety: **passed** for the disposable spike; hard cap,
  refusal, queue, lifecycle, crash recovery and 1-heavy + 2-light proven.
- G-05 — API and job core: **passed on loopback**; native jobs, auth,
  idempotency, admission, process cancellation, provenance, warnings, bounded
  request/upload/result memory, metrics and OpenAI chat adapter tested against
  the real route. Shutdown leaves no child worker alive.

## Next proof

Next planned vertical is G-06 (vision and documents), after an explicit next-lot
decision. It must reuse the G-05 capability/job boundary and compare native
text extraction, OCR/layout specialists and the measured general VLM without
claiming universal vision quality.

## Blockers and risks

No blocker remains in the authorised G-02 through G-05 lot. Permanent service,
live UI wiring, Hermes integration and consumer adoption remain intentionally
unstarted behind later gates.

Risks: platform sprawl, false vision equivalence, resource interference, consumer/model coupling, licence drift, public-data leakage, hidden cloud fallback and premature GPU-specific architecture.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- General shared runtime; Sillage integrates later as one consumer.
- Useful operations UI desired.
- Open-source licence authorised.
