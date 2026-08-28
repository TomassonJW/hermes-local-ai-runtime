# ADR-0012 - whisper.cpp batch transcription first, no streaming

- Status: Accepted
- Date: 2026-08-28
- Decision owners: Hermes (implementation), Thomas Jankowski (lot GO)
- Related gates: G-08
- Evidence: `operations/G08-AUDIO-2026-08-28.md`

## Context

G-08 must add local speech-to-text on the G-05 job core. Whisper Large is too
heavy for the default 8 vCPU / 16 GiB shared VM. Streaming is a later contract.

## Options considered

1. Whisper Large as default - rejected on memory and RTF.
2. whisper.cpp tiny/base/small, batch jobs, energy VAD and 30 s chunks.
3. Qwen3-ASR 0.6B - not packaged on this VM, comparison skipped.

## Decision

`audio.transcribe` is a G-05 job. Default `balanced` route is whisper.cpp `base`.
`fast` is `tiny`. `small` is measured but not default. Silence and empty audio
return unsupported. Streaming remains planned. Binary and model paths come from
the route/environment, never from the consumer.

## Consequences

Consumers get timestamps, language hint, cancellation and bounded duration
(15 min). Identifier-level French accuracy on espeak fixtures is not claimed.

## Validation

Falsify if silence is transcribed as words, if Large is the default, if a
permanent ASR service is installed, or if request audio is logged.

## Rollback

Remove the whisper-cpp worker and `/v1/audio/transcriptions`. G-05 to G-07 stay.
