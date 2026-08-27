# G-02 — Read-only environment probe — 2026-08-27

Refreshed immediately after UI-00 acceptance, before any engine work. All
queries read-only. Complements `LIVE-PROFILE-2026-08-27.md` (G-01) with the
items G-02 requires explicitly.

## OS and architecture

- Ubuntu 24.04.4 LTS (Noble), x86_64, systemd 255.
- Kernel: 6.8 series (HWE for this VM generation).

## CPU

- 10 vCPU allocated to the VM (host family AMD Ryzen 9 7900, 12C/24T — host
  capacity is NOT VM allocation).
- Feature flags relevant to inference: AVX, AVX2, F16C, FMA, full AVX-512
  (F/BW/CD/DQ/VL/IFMA/VBMI/VNNI/BITALG/VPOPCNTDQ/BF16).

## Memory

- ~19.5 GiB RAM allocated (OS reports 19 Gi total).
- **No swap device.** Overcommit fails hard (OOM-kill); admission-before-start
  is mandatory, not cosmetic.
- At probe time: ~2.8 GiB used, ~16 GiB available, PSI memory some/full = 0.00.

## Disk

- Root volume 61 GiB, ~56 GiB free at probe time.
- Spike working area (disposable, outside Git):
  `<project workspace>/spike-g03/` with `bin/`, `models/`, `logs/`, `results/`.
- Candidate model-store quota for later installation: 30 GiB (unchanged
  proposal from the hardware profile).

## Headroom discipline for the spike

- The VM hosts live Hermes services. Spike processes are bounded with
  `systemd-run --user --scope -p MemoryMax=` when exercising limits, bound to
  loopback, and torn down after each scenario.
- Guardrail during all spike work: keep ≥ 4 GiB memory available for
  non-runtime services; abort any scenario that pushes PSI memory full > 0.5
  sustained.

## Prerequisites present (read-only inventory)

| Tool | Version | Relevant to |
| --- | --- | --- |
| Python | 3.11.15 (session) / 3.12.3 (distribution) | control plane, harness |
| Node.js / pnpm | 22.23.1 / 10.34.5 | UI |
| git | 2.43.0 | everything |
| gcc / make | 13.3.0 / 4.3 | source builds if needed |
| cmake | absent | not needed: official pinned llama.cpp binaries link clean (`ldd` OK) |
| podman | 4.9.3 | LocalAI comparison, packaging candidates |
| docker | absent | — |
| systemd-run | 255 | bounded scopes for G-04 |

## Verdict

G-02 pass criteria met: public-safe profile recorded, VM allocation
distinguished from host capacity, prerequisites inventoried, no mutation
performed. The environment matches deployment profile A assumptions with two
favorable deltas (10 vCPU, ~19.5 GiB) and one tightened constraint (no swap).
