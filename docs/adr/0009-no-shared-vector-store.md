# ADR-0009 — No shared vector store initially

- Status: Accepted
- Date: 2026-08-27
- Related gates: G-07, G-10

Embeddings/reranking are shared computation. A central vector DB introduces ownership, retention, tenant isolation, backup and deletion scope unrelated to inference.

Runtime computes vectors and reranks bounded candidates; consumers store/index. A shared knowledge service would be a separate explicit product capability.
