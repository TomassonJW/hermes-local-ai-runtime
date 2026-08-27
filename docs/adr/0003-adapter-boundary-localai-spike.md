# ADR-0003 — Adapter boundary and mandatory LocalAI comparison

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-03

LocalAI may eliminate custom integration but may import excessive scope. Domain model stays engine-neutral. First spike compares equivalent bounded tasks through llama.cpp/lifecycle, LocalAI and direct specialists for install, idle/peak resources, cold/warm latency, cancellation, metrics, pinning, licence, recovery, API semantics and maintenance.

LocalAI may become an execution substrate; no adapter may redefine capability semantics. Publish measured ADR update before permanent packaging.
