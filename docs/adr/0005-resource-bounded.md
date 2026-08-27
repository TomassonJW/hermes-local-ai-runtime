# ADR-0005 — Resource-bounded CPU-first execution

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-02, G-04

The runtime shares 8-vCPU/16-GiB VM with other services. Resource admission is invariant. Candidate limits: 4 normal cores, burst 6, 8 GiB soft/10 GiB hard, one heavy, two light, queue 8, no sustained swap, lazy pressure-unload.

Some requests queue/reject; model maximum context is irrelevant absent route approval; batch yields to interactive. Amend only from repeated measurements.
