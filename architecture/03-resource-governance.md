# Resource governance

## Target

Existing shared VM: 8 vCPU, 16 GiB RAM, no GPU. Host's 12-core/24-thread CPU and 30 GiB RAM do not override VM allocation.

## Initial candidate budget

```yaml
cpu:
  normal_cores: 4
  burst_cores: 6
memory:
  soft_gib: 8
  hard_gib: 10
concurrency:
  heavy: 1
  light: 2
queue:
  max_jobs: 8
swap:
  sustained_growth_allowed: false
```

Values remain provisional until live gates.

## Resource classes

`tiny`: native text/health/metadata. `light`: OCR page, embedding batch, rerank. `medium`: multipage OCR/layout, short ASR. `heavy`: VLM/LLM or long ASR. `exclusive`: conversion/benchmark in maintenance window.

Admission uses available memory/pressure, CPU pressure, swap delta, model residency, estimated model/KV memory, input/context/image/page/audio size, leases, quota, queue age and maintenance state.

Outcomes: admitted, queued, resource/policy/input rejected, degraded route available, retry-after. Never start and hope OS resolves overcommit.

## Residency candidates

Native extractors resident; tiny OCR/compact embeddings resident only if measured; reranker long TTL; 0.6–1.2B text lazy 15 min; 1.5–2B VLM lazy 5 min; speech lazy 10 min; rare heavy 2 min. Pressure overrides TTL; drain after leases.

## Context/cache

Approved task bounds, not advertised maximums: classification 2k–4k; structured text 4k; single image 4k–8k; dense document 8k–16k; long document chunk/aggregate.

KV F16 reference, Q8 balanced candidate, Q4 only model-specific memory-constrained preset passing regressions. Image pixels/tokens explicit and transformations reported.

Evaluate systemd/cgroup limits and engine thread counts. Avoid multiplying internal threads by concurrent jobs. Under pressure refuse batch, stop prewarm, unload idle heavy, keep health/status/cancel interactive, reject rather than swap-thrash.
