# Mission 08 — Hardening, packaging, and release

## Goal

Turn the internal runtime into a reproducibly installable open-source system.

## Work

- supported OS/architecture matrix;
- install, update, uninstall;
- rootless/least-privilege service choice;
- systemd/cgroup policies;
- model-store tooling;
- migrations and backup;
- generated third-party notices;
- SBOM and dependency scanning;
- signed/checksummed release artefacts where feasible;
- API compatibility tests;
- private/tailnet deployment guide;
- support bundle;
- security review;
- public synthetic evaluation;
- contribution and release process.

## Internal shared-runtime proof

Before public release, integrate two independent consumers and replace one model/engine without changing them.

## Acceptance

G-09, G-10, and then G-11.
