# Source map

This map explains how source classes affected the compiled repository without exposing private source content.

| Compiled area | Source inputs | Distillation |
| --- | --- | --- |
| Product name and public status | Thomas's explicit 27 Aug 2026 decision | `README`, manifest, licence |
| Shared AI kernel scope | Current conversation and earlier architecture exploration | product vision, capability map, ADR-0001 |
| Not Sillage-specific | Sillage status/handoff and explicit decision | non-goals, consumer example, ADR-0006 |
| CPU-first target | Server inventory and explicit decision | hardware profile, resources, missions |
| Future GPU | Explicit product decision | generic worker/placement architecture |
| Vision replacement limits | Official Hermes behaviour, official small-model cards, product challenge | quality/fallback policy, ADR-0008, vision benchmark |
| OCR/document candidates | Official PaddleOCR documentation | registry candidates and G-06 |
| Embedding/reranking | Official Qwen and ONNX ecosystem evidence | capability definitions and mission 05 |
| Audio | official whisper.cpp and Qwen ASR evidence | audio capability and mission 06 |
| Hermes custom/local integration | official Hermes documentation | architecture 07 and integration templates |
| Agentic handoff | private agentic canon 0.5.0 | AGENTS, manifest, gates, state, handoff, missions |
| UI process | canonical UI design 1.3.0 | local UI contract and UI-00 stop |
| Open-source governance | public software project requirements | Apache-2.0, security, contributing, CI |

## Authority rule

Private sources motivated the product but are not runtime dependencies. If a public contributor cannot access the private canons, the local product, architecture, UI contract, gates, and contributor rules remain sufficient.

## Drift rule

A major product amendment is written as an explicit repository diff with source and impact. It does not silently overwrite existing decisions.
