# Deployment profiles

## A — Hermes CPU VM

Ubuntu 24.04, x86_64, 8 vCPU, 16 GiB RAM, no GPU, shared VM, local/tailnet. One heavy inference, 10 GiB hard runtime candidate, model-store quota, separate worker environments, loopback default, no Proxmox change.

Defined in `config/hardware-profiles/hermes-cpu-8vcpu-16gib.yaml`.

## B — Generic small CPU

4 cores/8 GiB for specialists/smoke tests. Tiny OCR/vector likely; 2B VLM not guaranteed; probe may disable heavy routes.

## C — Future local GPU

Disabled. Requires exact device/VRAM, host RAM, drivers/backend, power/cooling, isolation/passthrough and measured workloads. Same API/registry; placement changes.

## D — Tailnet execution worker

Disabled. Requires mutual auth, encryption, heartbeat, capability advertisement, data-class policy, cancellation/orphan handling and version compatibility. Tailnet membership alone is not trust.

## Packaging candidates

Compare native binaries + Python control plane + systemd; rootless containers; hybrid native binaries/isolated Python workers; LocalAI container substrate. Criteria: install/remove, model persistence, cgroups, GPU evolution, recovery, upgrade rollback, pinning and surface area.

Candidate paths separate `/etc` config, `/var/lib` state, `/var/cache`, `/var/log`, model store and `/run`; actual paths are implementation decisions and must not assume private Hermes layout.
