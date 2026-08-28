# State

Last updated: 2026-08-28 13:10 CEST (G-08 audio lot)

## Phase

Phases 0-6 complete through G-08 on loopback. UI-00 remains accepted simulated
shell. No permanent runtime deployment. Not a daily-use program yet.

## Product status

- Repository public; product baseline `0.1.0`, API/job-core candidate `0.2.0-dev`.
- Product baseline: `19070875f0c80e7799f394f6d4d16b481bd9be21` on `baseline/v0.1.0`.
- Operational owner: Hermes (canonical productions clone on the Hermes VM).
- Current `main`: `3f496c9`.
- G-05 delivery: `952614e`; G-06 delivery: `faa6dac`; G-07 delivery: `fb4e059`; G-08 delivery: `3f496c9`.
- G-08 source: `runtime/audio.py`, whisper.cpp worker, `/v1/audio/transcriptions`.
  Evidence: `operations/G08-AUDIO-2026-08-28.md`.
- Permanent installation, Hermes config changes, live UI-01, production
  consumers: none. Spike artefacts and model weights remain outside Git.

## Current truth

Shared local AI capability kernel. Audio is a batch job: whisper.cpp `base` is
the default local route. Silence is unsupported, not invented. Streaming and
Qwen3-ASR are not implemented. Whisper Large is not the default.

## Gates

- G-00 to G-07 and UI-00: **passed** (unchanged).
- G-08 - Audio: **passed** as batch whisper.cpp with a declared default
  (espeak fixture; identifier recovery not claimed; Qwen3-ASR not packaged).
- G-09 to G-11: **not started**.

## Next proof

G-09 (packaging) only after an explicit next-lot decision.
Mission: `missions/08-hardening-packaging-release.md`.

## Blockers and risks

No blocker in the authorised G-08 lot. Permanent service, live UI wiring,
Hermes integration and consumer adoption remain unstarted.

Risks: false ASR quality, resource interference, consumer/model coupling,
public-data leakage, hidden cloud fallback.

## Human decisions already made

- Project name: Hermes Local AI Runtime.
- Public repository.
- CPU-first inside Hermes; future GPU required but not immediate.
- UI-00 accepted.
- G-02 through G-08 authorised. G-08 closed as batch whisper.cpp, not as
  streaming or Whisper Large.
- Hub top-bar shortcut requested and delivered.
