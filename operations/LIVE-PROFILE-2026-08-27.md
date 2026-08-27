# Live VM profile — 2026-08-27 (read-only, redacted)

Collected during G-01 takeover preflight. All measurements are read-only OS queries.
No package was installed on the system, no service created, no port opened, no
model downloaded. An ephemeral Python virtualenv (pinned `requirements-dev.txt`)
was created outside the repository, in the local workspace, solely to run the
prescribed validator and tests; it is disposable and touches no system path.

## Measured VM allocation

| Item | Pinned profile (`hermes-cpu-8vcpu-16gib.yaml`) | Measured live | Delta |
| --- | --- | --- | --- |
| OS | Ubuntu 24.04 | Ubuntu 24.04.4 LTS (Noble) | match |
| Architecture | x86_64 | x86_64 | match |
| vCPU | 8 | **10** | **+2 (favorable)** |
| RAM total | 16 GiB | **~19.5 GiB** (OS reports 19 Gi) | **+~3.5 GiB (favorable)** |
| Swap | growth forbidden | **0 B configured (no swap device)** | note S-1 |
| GPU | none | none detected (no NVIDIA/AMD device, `nvidia-smi` absent) | match |
| Host family | Ryzen 9 7900 | AMD Ryzen 9 7900 visible as vCPU model | match |

Host capacity is not VM allocation; only the figures above are available to the runtime.

## CPU features (relevant to inference engines)

`avx avx2 f16c fma avx512f avx512bw avx512cd avx512dq avx512vl avx512ifma
avx512vbmi avx512_vnni avx512_bitalg avx512_vpopcntdq avx512_bf16`

Full AVX-512 family incl. VNNI and BF16 — favorable for llama.cpp CPU builds (G-03).

## Headroom at collection time

- Load average: 0.18 / 0.37 / 0.53 on 10 vCPU.
- Memory: ~2.8 GiB used, ~16 GiB available (buff/cache reclaimable).
- PSI memory: some avg10=0.00, full avg10=0.00. PSI CPU: some avg10=0.00.
- Disk (root volume): 61 GiB total, **56 GiB free**.

## Toolchain inventory (read-only)

| Tool | Status |
| --- | --- |
| Python | 3.11.15 (`python3` in session PATH); PEP 668 managed environment |
| git | 2.43.0 |
| Node.js / npm | v22.23.1 / 12.0.2 — sufficient for UI-00 without new system packages |
| gcc / make | 13.3.0 / 4.3 |
| cmake | absent (needed later for engine spike builds — G-03 concern, not UI-00) |
| docker | absent |
| podman | 4.9.3 |
| systemd | 255 |

## Contradictions

- **C1 — vCPU**: pinned 8, measured 10. Favorable. Conservative budget
  (4 normal / 6 burst cores) remains valid and unchanged. Hardware-profile
  update is proposed to Thomas, not applied.
- **C2 — RAM**: pinned 16 GiB, measured ~19.5 GiB. Favorable. Soft 8 GiB /
  hard 10 GiB budget remains valid and unchanged.
- **C3 — swap**: no swap device exists. "No sustained swap growth" is trivially
  satisfied, but memory overcommit now fails hard (OOM-kill) instead of
  degrading. G-04 hard memory limits and admission-before-start become more
  important, not less.

Per G-01, a material contradiction requires a stop when it invalidates safety
assumptions. C1/C2 are favorable capacity deltas and C3 tightens (not loosens)
an existing constraint; UI-00 has no dependency on any of them (static frontend,
fixture data only). Work therefore continues to UI-00, and the profile decision
is escalated with the UI-00 verdict request.

## Unknowns

- U1: distribution-default Python vs session Python (3.11.15) — final runtime
  Python is an implementation ADR after the engine spike.
- U2: container packaging path must account for podman (docker absent) — G-03/G-09.
- U3: reachability policy of the authorised private surface was not probed
  (no network mutation in preflight); UI-00 serving uses the existing
  authorised private surface only.
- U4: cmake absent — engine spike (G-03) will need it or prebuilt binaries;
  installation belongs to that gate, not to preflight.
