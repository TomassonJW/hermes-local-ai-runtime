# Hermes integration

This directory contains the future Hermes adapter, not an instruction to alter the live Hermes installation during bootstrap.

## Intended surfaces

1. custom OpenAI-compatible endpoint for main/local models;
2. auxiliary vision endpoint for text-only main models;
3. MCP or native tools for OCR, document, embedding, reranking, audio, and operations;
4. a thin global Hermes skill.

## Skill installation target

Candidate skill source:

```text
integration/hermes/skill/hermes-local-ai-runtime/SKILL.md
```

After G-09 and an explicit integration mission, installation may copy or link the skill into a Hermes skill directory and verify it in a fresh session. Project-local trust and global installation must follow the installed Hermes version's documented process.

## Design rule

The skill teaches discovery and integration discipline. It does not embed:

- model lists;
- private URLs;
- secrets;
- runtime product constitution;
- a second API specification;
- application-specific business rules.

## Version compatibility

Record and test:

- Hermes version;
- config schema;
- custom provider base URL;
- image request format;
- auxiliary vision route;
- OpenAI compatibility endpoints;
- MCP transport;
- timeout and fallback semantics.

Templates in `config/hermes/` and `CONFIG.example.yaml` are conceptual until tested against the installed version.
