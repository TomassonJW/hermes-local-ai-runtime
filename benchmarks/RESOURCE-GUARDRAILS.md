# Resource guardrail benchmark

## Purpose

Prove that accepted AI work does not make the shared Hermes VM unstable.

## Baseline capture

Before AI load:

- CPU pressure and load;
- memory available and pressure;
- swap used and rate of change;
- disk I/O and free space;
- representative Hermes service response latency;
- process inventory summarised without secrets.

## Scenarios

1. one tiny request;
2. light embedding batch;
3. OCR page;
4. heavy cold VLM request;
5. heavy warm VLM request;
6. heavy request plus two light requests;
7. queue overflow;
8. cancellation during load;
9. cancellation during inference;
10. worker crash;
11. memory-pressure forced unload;
12. repeated load/unload;
13. benchmark/batch while interactive request arrives;
14. control-plane restart with queued/running jobs.

## Pass signals

- hard memory limit respected;
- no OOM;
- no sustained swap growth;
- queue/cancel/status endpoints stay responsive;
- representative services stay within accepted latency;
- admission rejects before harmful pressure;
- worker is reaped after crash/cancel;
- state converges after restart;
- no model remains loaded past pressure/TTL policy without lease.

## Report

Record exact commands and environment in a private operational report. Public summary contains only hardware profile ID, aggregate numbers, runtime versions, and conclusions.
