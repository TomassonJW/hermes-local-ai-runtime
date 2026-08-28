# Changelog

All notable changes to Hermes Local AI Runtime will be documented here.

The project follows Semantic Versioning once executable public releases begin. Bootstrap versions describe the product constitution and may change before API stability is declared.

## [Unreleased]

### Added

- G-05 loopback capability/job core (native `/api/v1` plus OpenAI chat adapter);
- G-06 vision and document workers behind that job core;
- G-07 embeddings, bounded rerank, result cache and consumer persist helpers;
- G-08 whisper.cpp batch transcription and `/v1/audio/transcriptions`;
- per-task-family registry (`registry/task-families.yaml`);
- synthetic public fixture generator for vision/document evaluation.

### Limits

- G-06 is not universal vision. PaddleOCR, private corpora, fine UI review,
  charts and multi-image reasoning were not measured.
- G-07 is not a vector database. FastEmbed is not wired. French queries may
  still rank an English invoice first inside the same family.
- G-08 is batch whisper.cpp. Silence abstains. Identifier-level French on
  espeak is not claimed. Streaming and Qwen3-ASR are not implemented.
- No permanent service, live UI-01, or Hermes config mutation.

## [0.1.0] - 2026-08-27

### Added

- complete product and architecture bootstrap for a shared local AI capability runtime;
- CPU-first target profile for the existing Hermes VM;
- future GPU and distributed-worker boundary;
- native capability API and OpenAI-compatible facade contracts;
- model registry, lifecycle, licence, benchmark, provenance, and resource-governance rules;
- local-first vision policy with explicit quality limits and fallback gates;
- OCR, document, embedding, reranking, vision, object/image, and speech capability map;
- operations UI contract and mandatory UI-00 stop;
- Hermes integration and candidate skill contract;
- development missions, roadmap, backlog, gates, state, handoff, and validation tooling.

### Not implemented

- runtime backend;
- workers or model downloads;
- UI;
- installation or deployment;
- Hermes configuration mutation;
- consumer integration.
