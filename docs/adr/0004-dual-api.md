# ADR-0004 — Native capability API plus compatibility adapters

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-05

Hermes/ecosystem understand OpenAI APIs, while OCR/documents/jobs/evidence/lifecycle/resources do not fit chat semantics.

Create normative native `/api/v1`, OpenAI-compatible `/v1` adapters and optional MCP tools. Native result carries evidence, warnings, review and provenance. More contract work buys clear semantics and Hermes compatibility without sacrificing specialisation.
