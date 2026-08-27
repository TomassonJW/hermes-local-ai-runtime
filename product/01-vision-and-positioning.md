# Vision and positioning

## Problem

Local AI capabilities are useful across many applications, but each integration tends to rebuild model discovery/downloads, engine installation, conversion/quantisation, prompts/schemas, context and cache settings, load/unload/TTL, CPU/RAM/GPU limits, licence/provenance, benchmarks, authentication and application adapters.

This duplication increases delivery time, drift, security risk and mental load. It also makes one application accidentally responsible for shared infrastructure.

## Product vision

Provide one dependable local AI control plane that is easy for Hermes to discover while building software, simple for applications to call, conservative with CPU/RAM, honest about uncertainty, open-source/installable, future-GPU-ready, and independent from any single model, runtime, application or datastore.

## What kernel means

Kernel is product language for the smallest shared control surface every local AI consumer can rely on. It is not an operating-system kernel and must not run with hypervisor or unnecessary host privileges.

The kernel owns capability identity/version, route/policy resolution, jobs, resource admission, worker lifecycle, model registry, cache/provenance and compatibility surfaces. Workers own inference. Applications own business logic and persistence.

## Positioning

The project sits between low-level inference engines, broad all-in-one AI platforms and application-specific integrations. It does not compete with llama.cpp, PaddleOCR, ONNX Runtime, whisper.cpp or model authors; it composes them.

It may use LocalAI if that materially reduces custom code without breaking product/resource/security boundaries.

## Why not LM Studio as production authority

LM Studio remains useful as a workstation laboratory for visual testing and parameter exploration. Production must be headless, reproducible, scriptable, inspectable, open-project-compatible and governed by repository configuration/benchmarks rather than desktop state.

## Why not one VLM for everything

A general VLM is valuable for open questions and semantic reasoning but is not automatically best for exact OCR, document layout, object coordinates, image similarity, duplicate detection, low-latency classification or deterministic numeric extraction. Routing preserves specialists and generalists.

## Value

Immediate value is internal: less repeated integration, lower cloud-token use on bounded tasks, local privacy, reusable evaluation/resource policy, and faster future Hermes applications. Public revenue is not an initial success criterion.
