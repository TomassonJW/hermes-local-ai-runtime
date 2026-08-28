# Decisions

Accepted and candidate architecture decisions live in [`docs/adr/`](docs/adr/).

Current accepted bootstrap decisions:

- capability kernel rather than model-manager product;
- `llama.cpp` as the preferred first general inference candidate;
- LocalAI comparison required before implementation lock-in;
- native capability API plus compatibility adapters;
- resource-bounded CPU-first profile;
- model-agnostic consumers;
- Apache License 2.0 for original repository work;
- local-first vision with explicit quality/fallback policy;
- G-06 vision/document workers reuse the G-05 job core (ADR-0010);
- G-07 embeddings and rerank are computation, not a vector DB (ADR-0011);
- G-08 audio is batch whisper.cpp, not streaming (ADR-0012);
- G-09 is a rootless prefix install; systemd is shipped not enabled (ADR-0013);
- G-10 consumers speak capabilities, not model files (ADR-0014);
- G-11 is a public source candidate, not production support (ADR-0015);
- UI-01 is a live loopback console, not production support (ADR-0016);
- systemd user services are enabled for the runtime and model router (ADR-0017),
  superseding the "shipped not enabled" clause of ADR-0013 and ADR-0016.

A decision becomes active only when its ADR status is `Accepted` or when this repository's product constitution explicitly makes it non-negotiable.
