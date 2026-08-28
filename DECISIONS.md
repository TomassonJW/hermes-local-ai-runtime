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
- G-06 vision/document workers reuse the G-05 job core (ADR-0010).

A decision becomes active only when its ADR status is `Accepted` or when this repository's product constitution explicitly makes it non-negotiable.
