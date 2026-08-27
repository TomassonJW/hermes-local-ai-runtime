# Future GPU and distributed workers

## Goal

Adding GPU improves placement, not consumer contracts.

Worker advertises ID/trust, OS/arch, CPU/RAM, accelerator vendor/device/memory/driver/backend, engines, immutable models, capability/presets, capacity/leases, data-class maximum and network class.

Resolver considers hardware requirement, data class, trust, model locality, queue/load, transfer size, latency and operator policy.

## NVIDIA versus AMD

No choice now. At acquisition compare exact VRAM/bandwidth, engine backend support, driver/kernel/virtualisation stability, formats/quantisation/multimodal, power/cooling/availability/price, maintenance and measured workloads rather than TOPS. Consumer API contains no CUDA/ROCm concepts.

## Placement

Possible GPU passthrough into existing VM, dedicated VM/LXC/host worker or local network worker. This is infrastructure work with backup/rollback/isolation; product repo does not authorise hypervisor changes.

Trusted workstation may register via tailnet only with mutual auth, trust record, data policy, cancellation/orphan handling. Offline worker disappearance never silently reroutes cloud.

Worker/control-plane protocol is versioned; incompatible worker quarantines.
