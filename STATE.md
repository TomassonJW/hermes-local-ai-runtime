# State

Last updated: 2026-08-27

## Phase

Compiled bootstrap, ready for Hermes takeover.

## Product status

- Repository public, version `0.1.0`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Bootstrap validator and five tests pass locally.
- GitHub Actions `validate-bootstrap` run `33108026212` completed successfully on the anchored baseline branch state.
- Implementation, installation, runtime service, model downloads, Hermes configuration changes, consumers and UI: none.
- Current authority: this repository.

## Current truth

The product is a shared local AI capability kernel for Hermes and other applications. It is not a Sillage feature and not a monolithic model server. It assembles replaceable engines and adds capability contracts, routing, resource admission, model governance, provenance, evaluation, compatibility APIs and operations.

The first deployment target is the existing Hermes VM with 8 vCPU, 16 GiB RAM and no GPU. The Proxmox host has more total CPU/RAM, but those resources are not automatically available inside the VM. The live profile must still be refreshed read-only during G-01/G-02.

## Gates

- G-00 — Bootstrap integrity: **passed**.
- G-01 — Hermes takeover: **active**.
- UI-00 — Operations shell: next visible lot after takeover.
- Runtime backend: blocked until Thomas explicitly accepts UI-00 and G-02 is current.

## Next proof

Hermes clones or updates safely, validates the repository, produces a coverage map, refreshes a redacted read-only environment profile, updates state/handoff, and makes no system mutation.

## Blockers and risks

No blocker for read-only takeover. UI-00 must be accepted before backend. Engine selection remains a measured spike.

Risks: platform sprawl, false vision equivalence, resource interference, consumer/model coupling, licence drift, public-data leakage, hidden cloud fallback and premature GPU-specific architecture.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- General shared runtime; Sillage integrates later as one consumer.
- Useful operations UI desired.
- Open-source licence authorised.
