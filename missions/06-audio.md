# Mission 06 — Speech transcription

## Goal

Add local speech-to-text under the same jobs, resources, provenance, and privacy model.

## Baseline

Measure `whisper.cpp` first because it is CPU-oriented, quantised, and operationally simple.

Candidate variants must be selected by measured French quality and real-time factor. Do not assume Whisper Large is appropriate for the initial 8-vCPU/16-GiB shared VM.

## Work

- supported audio formats and decode limits;
- VAD;
- chunking;
- batch job;
- timestamps;
- language hint/auto detection;
- cancellation;
- long-file temp storage;
- metadata-only logs;
- cold/warm and real-time factor;
- Qwen3-ASR 0.6B comparison after packaging and licence review;
- streaming design only after batch route is stable.

## Acceptance

G-08 passes with a declared default and explicit unsupported/resource-refused behaviour.
