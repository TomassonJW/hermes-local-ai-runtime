# Mission 00 — Takeover and read-only preflight

## Goal

Make Hermes the operational owner of the repository and replace stale assumptions with a public-safe read-only profile.

## Preconditions

- baseline recorded;
- GitHub access configured;
- no foreign uncommitted work;
- G-00 passes.

## Allowed

- clone/fetch/inspect Git;
- read repository and pinned canons;
- run repository validation;
- inspect OS/CPU/RAM/disk/process/resource state read-only;
- verify available build/container tools read-only;
- write public-safe reports in the repository;
- refine ADR proposals and mission plan.

## Forbidden

- package installation;
- model download;
- service creation/activation;
- firewall, proxy, Tailscale, Proxmox, or unrelated service change;
- opening a listener;
- reading secrets or private corpora;
- altering Hermes config;
- application integration.

## Deliverables

- coverage map from requirements to files/gates;
- `operations/LIVE-PROFILE-YYYY-MM-DD.md` with redacted measurements;
- contradiction/unknown list;
- confirmed UI-00 plan;
- updated `STATE.md` and `HANDOFF.md`;
- focused commit and push.

## Acceptance

- repository remains public-safe;
- no side effect beyond Git files;
- target profile distinguishes VM allocation from host capacity;
- next mission is UI-00;
- no backend work begins.
