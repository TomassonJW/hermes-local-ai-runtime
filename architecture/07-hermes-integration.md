# Hermes integration

## Surfaces

### Auxiliary vision

For text-only main model. Hermes points auxiliary vision at runtime OpenAI endpoint. Runtime receives image + question and returns direct answer. Main model receives text, not pixels; answer must preserve evidence/uncertainty. Template: `config/hermes/auxiliary-vision.example.yaml`.

### Custom main model

When runtime hosts Hermes main text/multimodal model. Hermes points custom provider to runtime. If main model and Hermes path are multimodal, image content remains in main request. Template: `config/hermes/main-model.example.yaml`.

### MCP/tool capabilities

Explicit OCR, document parse, embedding, rerank, audio and status operations fit structured tools rather than chat semantics.

### Thin skill

Teaches discovery, integration and boundaries. It does not duplicate constitution, carry model lists or private URLs.

## Routing patterns

Text-only: image question -> Hermes aux vision -> local `vision.analyze` -> text answer/warnings -> main model.

Multimodal main: image question -> runtime OpenAI facade -> approved local multimodal route -> final answer.

Specialist: Hermes tool `document.parse` -> typed regions/fields/provenance -> Hermes/application logic.

## Fallback ownership

Runtime owns specialist-to-general-local fallback. Hermes owns explicit local-to-remote model fallback when conversation policy permits. Installation enables none by default. Avoid double retries.

## Compatibility

Pin/test Hermes version for custom base URL, vision encoding, auxiliary config, model IDs, streaming, MCP/tool transport and error/timeout translation. Upgrade does not imply compatibility.
